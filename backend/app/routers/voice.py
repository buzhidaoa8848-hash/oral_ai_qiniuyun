"""Voice interaction routes: transcribe + full voice-turn with latency tracking."""

import logging
import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from ..config import settings
from ..database import get_session as get_db_dep
from .. import models as m, schemas, services
from ..conversation_agent import ConversationAgent
from ..providers.stt import get_stt_provider
from ..providers.pronunciation import get_pronunciation_provider

logger = logging.getLogger("scenetalk.voice")
router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """Transcribe an audio blob. Returns the text and STT latency."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/webm"

    stt = get_stt_provider()
    t0 = time.perf_counter()
    transcript = stt.transcribe(audio_bytes, mime_type)
    stt_ms = round((time.perf_counter() - t0) * 1000)

    return {
        "transcript": transcript,
        "stt_latency_ms": stt_ms,
    }


@router.post("/sessions/{session_id}/voice-turn")
async def voice_turn(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_dep),
):
    """Full voice turn:
    1. Transcribe audio → STT latency
    2. Run ConversationAgent → LLM latency
    3. Persist turns + latency metrics
    4. Return transcript, AI reply, latencies
    """
    try:
        return await _voice_turn_impl(session_id, file, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Voice turn unexpected error — session=%s", session_id)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_code": "voice_turn_internal_error",
                "message": f"语音处理暂时失败: {str(e)[:200]}。请重试或使用文字输入继续练习。",
                "fallback_available": True,
            },
        )


async def _voice_turn_impl(
    session_id: uuid.UUID,
    file: UploadFile,
    db: Session,
):
    """Core voice-turn logic, extracted for clean exception handling."""
    t_start = time.perf_counter()

    # ── 0. Load session + scene ──────────────────────────────
    ps = services.get_session(session=db, session_id=session_id)
    if not ps:
        raise HTTPException(status_code=404, detail="PracticeSession not found")

    scene = services.get_scene_card(session=db, scene_id=ps.scene_card_id)
    if not scene:
        raise HTTPException(status_code=404, detail="SceneCard not found")

    # ── 1. STT ───────────────────────────────────────────────
    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/webm"

    # Reject very short / empty audio
    if len(audio_bytes) < 500:
        raise HTTPException(
            status_code=400,
            detail="录音太短或为空，请至少录制 1 秒后重试。",
        )

    # Reject near-silent audio (WAV header + all-zero samples)
    if _audio_is_silent(audio_bytes, mime_type):
        raise HTTPException(
            status_code=400,
            detail="未检测到有效语音。请确保：\n1. 麦克风未被静音\n2. 录音时大声说出你的回答\n3. 如无法使用语音，请使用文字输入模式",
        )

    stt = get_stt_provider()
    t_stt_start = time.perf_counter()
    stt_degraded = False
    try:
        transcript = stt.transcribe(audio_bytes, mime_type)
    except Exception as e:
        logger.warning("STT failed, falling back to mock — error: %s", e)
        from ..providers.stt.mock_stt import MockSTTProvider
        stt = MockSTTProvider()
        transcript = stt.transcribe(audio_bytes, mime_type)
        stt_degraded = True
    stt_latency_ms = round((time.perf_counter() - t_stt_start) * 1000)

    # ── 1b. Pronunciation evaluation ─────────────────────────
    audio_dur = len(audio_bytes) / 16000.0  # rough estimate: 16kHz mono = 16KB/s
    pron_provider = get_pronunciation_provider()
    t_pron_start = time.perf_counter()
    try:
        pron_result = pron_provider.evaluate(audio_bytes, transcript, audio_dur)
    except Exception:
        logger.exception("Pronunciation evaluation failed — using fallback")
        from ..providers.pronunciation.fallback_pronunciation import FallbackPronunciationProvider
        fallback = FallbackPronunciationProvider()
        pron_result = fallback.evaluate(audio_bytes, transcript, audio_dur)
    pron_latency_ms = round((time.perf_counter() - t_pron_start) * 1000)

    # ── 2. ConversationAgent ─────────────────────────────────
    history_rows = db.exec(
        select(m.ConversationTurn)
        .where(m.ConversationTurn.session_id == session_id)
        .order_by(m.ConversationTurn.turn_index)
    ).all()

    next_index = max((t.turn_index for t in history_rows), default=-1) + 1
    history = [{"role": t.role, "message": t.message} for t in history_rows]

    scene_dict = {
        "title": scene.title,
        "scene_type": scene.scene_type,
        "style": scene.style,
        "difficulty": scene.difficulty,
        "ai_role": scene.ai_role,
        "user_role": scene.user_role,
        "task_goal": scene.task_goal,
        "opening_question": scene.opening_question,
        "follow_up_strategy": scene.follow_up_strategy,
        "must_cover_points": scene.must_cover_points,
    }

    agent = ConversationAgent()
    t_llm_start = time.perf_counter()
    try:
        ai_reply = agent.reply(scene=scene_dict, history=history, user_utterance=transcript)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM failed: {e}. Please try again.",
        )
    llm_latency_ms = round((time.perf_counter() - t_llm_start) * 1000)

    # ── 3. Persist turns ─────────────────────────────────────
    user_turn, ai_turn = agent.summarize_turn(
        user_message=transcript,
        ai_reply=ai_reply,
        turn_index=next_index,
        session_id=session_id,
    )
    db.add(user_turn)
    db.add(ai_turn)

    # ── 4. Persist latency metrics ───────────────────────────
    e2e_ms = round((time.perf_counter() - t_start) * 1000)

    stt_metric = m.LatencyMetric(
        session_id=session_id,
        turn_id=user_turn.id,
        provider=settings.stt_provider,
        capability="stt",
        duration_ms=stt_latency_ms,
        success=not stt_degraded,
    )
    llm_metric = m.LatencyMetric(
        session_id=session_id,
        turn_id=ai_turn.id,
        provider=settings.llm_provider,
        capability="llm",
        duration_ms=llm_latency_ms,
        success=True,
    )
    tts_metric = m.LatencyMetric(
        session_id=session_id,
        turn_id=ai_turn.id,
        provider="browser-tts",
        capability="tts",
        duration_ms=0,  # browser-side, filled by frontend
        success=True,
    )
    pron_metric = m.LatencyMetric(
        session_id=session_id,
        turn_id=user_turn.id,
        provider=pron_result.provider_name,
        capability="pronunciation",
        duration_ms=pron_latency_ms,
        success=True,
    )
    db.add_all([stt_metric, llm_metric, tts_metric, pron_metric])
    db.commit()
    db.refresh(user_turn)
    db.refresh(ai_turn)

    # ── Run evaluation pipeline ──────────────────────────────
    from ..agents.pipeline import EvaluationPipeline, build_eval_context

    profile = services.get_profile(session=db, profile_id=ps.profile_id)
    eval_ctx = build_eval_context(
        user_message=transcript,
        ai_reply=ai_reply["reply"],
        scene=scene,
        turn_index=next_index,
        session_id=session_id,
        profile=profile,
    )
    pipeline = EvaluationPipeline()
    eval_result = pipeline.run(
        db=db,
        user_turn_id=user_turn.id,
        ctx=eval_ctx,
        pronunciation_score=pron_result.pronunciation_score,
        fluency_score=pron_result.fluency_score,
        phoneme_feedback=pron_result.phoneme_feedback,
        is_pron_estimated=pron_result.is_estimated,
    )
    light_hints = eval_result.light_hints

    # ── 5. Build response ────────────────────────────────────
    def _to_read(t: m.ConversationTurn) -> schemas.ConversationTurnRead:
        return schemas.ConversationTurnRead(
            id=t.id,
            session_id=t.session_id,
            turn_index=t.turn_index,
            role=t.role,
            message=t.message,
            intent=t.intent,
            based_on_user_point=t.based_on_user_point,
            next_goal=t.next_goal,
            should_interrupt=t.should_interrupt,
            audio_url=t.audio_url,
            transcript=t.transcript,
            created_at=t.created_at,
        )

    return {
        "transcript": transcript,
        "reply": ai_reply["reply"],
        "intent": ai_reply.get("intent", ""),
        "based_on_user_point": ai_reply.get("based_on_user_point", ""),
        "next_goal": ai_reply.get("next_goal", ""),
        "should_interrupt": ai_reply.get("should_interrupt", False),
        "is_final": ai_reply.get("intent") == "close_session",
        "user_turn": _to_read(user_turn),
        "ai_turn": _to_read(ai_turn),
        "latency": {
            "stt_ms": stt_latency_ms,
            "pron_ms": pron_latency_ms,
            "llm_ms": llm_latency_ms,
            "tts_ms": 0,  # filled by frontend
            "e2e_ms": e2e_ms,
        },
        "pronunciation": pron_result.to_dict(),
        "stt_degraded": stt_degraded,
        "light_hints": light_hints,
        "evaluation": {
            "grammar": eval_result.grammar.model_dump(),
            "expression": eval_result.expression.model_dump(),
            "naturalness": eval_result.naturalness.model_dump(),
            "task_completion": eval_result.task_completion.model_dump(),
            "profile": eval_result.profile.model_dump(),
        },
    }


# ── Audio quality helpers ──────────────────────────────────────

def _audio_is_silent(audio_bytes: bytes, mime_type: str) -> bool:
    """Return True if the audio is essentially silent (all samples near zero).

    Only works reliably for WAV/PCM data. For other formats (webm/opus),
    we do a conservative check based on file size variance.
    """
    # WAV: check PCM samples after the 44-byte header
    if "wav" in mime_type.lower() and len(audio_bytes) > 100:
        return _wav_is_silent(audio_bytes)

    # For other formats, just check if it's suspiciously small
    return len(audio_bytes) < 2000


def _wav_is_silent(data: bytes) -> bool:
    """Check RMS of first 1 second of 16-bit PCM WAV data."""
    try:
        # Skip WAV header (44 bytes), read 16-bit PCM samples
        pcm_start = 44
        sample_count = min((len(data) - pcm_start) // 2, 16000)  # max 1 sec

        if sample_count < 100:
            return True  # too few samples = silent

        total = 0.0
        for i in range(sample_count):
            offset = pcm_start + i * 2
            # Little-endian 16-bit signed
            sample = int.from_bytes(data[offset:offset + 2], "little", signed=True)
            total += (sample / 32768.0) ** 2

        rms = (total / sample_count) ** 0.5

        # RMS < 0.005 is essentially silent (typical speech RMS > 0.02)
        return rms < 0.005
    except Exception:
        return False  # can't determine → let STT decide
