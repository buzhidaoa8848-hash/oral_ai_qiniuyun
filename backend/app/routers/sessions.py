"""PracticeSession CRUD routes + conversation endpoint."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..database import get_session as get_db_dep
from .. import models as m, schemas, services
from ..conversation_agent import ConversationAgent

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[schemas.PracticeSessionRead])
def list_sessions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_dep),
):
    items, _ = services.get_all_sessions(session=db, skip=skip, limit=limit)
    return items


@router.post("", response_model=schemas.PracticeSessionRead, status_code=201)
def create_session(data: schemas.PracticeSessionCreate, db: Session = Depends(get_db_dep)):
    return services.create_session(session=db, data=data)


@router.get("/{session_id}", response_model=schemas.PracticeSessionRead)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    ps = services.get_session(session=db, session_id=session_id)
    if not ps:
        raise HTTPException(status_code=404, detail="PracticeSession not found")
    return ps


@router.put("/{session_id}", response_model=schemas.PracticeSessionRead)
def update_session(session_id: uuid.UUID, data: schemas.PracticeSessionUpdate, db: Session = Depends(get_db_dep)):
    ps = services.update_session(session=db, session_id=session_id, data=data)
    if not ps:
        raise HTTPException(status_code=404, detail="PracticeSession not found")
    return ps


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    ok = services.delete_session(session=db, session_id=session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="PracticeSession not found")


# ── Conversation ───────────────────────────────────────────────

@router.get("/{session_id}/turns", response_model=list[schemas.ConversationTurnRead])
def get_turns(session_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    """Return all conversation turns for a session, ordered by turn_index."""
    turns = db.exec(
        select(m.ConversationTurn)
        .where(m.ConversationTurn.session_id == session_id)
        .order_by(m.ConversationTurn.turn_index)
    ).all()
    return list(turns)


@router.post("/{session_id}/turns", response_model=schemas.ConversationResponse)
def post_turn(
    session_id: uuid.UUID,
    req: schemas.ConversationRequest,
    db: Session = Depends(get_db_dep),
):
    """Send a user message and get the AI reply."""
    # ── Load session + scene ────────────────────────────────
    ps = services.get_session(session=db, session_id=session_id)
    if not ps:
        raise HTTPException(status_code=404, detail="PracticeSession not found")

    scene = services.get_scene_card(session=db, scene_id=ps.scene_card_id)
    if not scene:
        raise HTTPException(status_code=404, detail="SceneCard not found")

    # ── Load history ────────────────────────────────────────
    history_rows = db.exec(
        select(m.ConversationTurn)
        .where(m.ConversationTurn.session_id == session_id)
        .order_by(m.ConversationTurn.turn_index)
    ).all()

    next_index = max((t.turn_index for t in history_rows), default=-1) + 1

    history = [
        {"role": t.role, "message": t.message}
        for t in history_rows
    ]

    # ── Build scene dict ────────────────────────────────────
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

    # ── Generate reply ──────────────────────────────────────
    agent = ConversationAgent()
    ai_reply = agent.reply(
        scene=scene_dict,
        history=history,
        user_utterance=req.message,
    )

    # ── Persist turns ───────────────────────────────────────
    user_turn, ai_turn = agent.summarize_turn(
        user_message=req.message,
        ai_reply=ai_reply,
        turn_index=next_index,
        session_id=session_id,
    )
    db.add(user_turn)
    db.add(ai_turn)
    db.commit()
    db.refresh(user_turn)
    db.refresh(ai_turn)

    # ── Run evaluation pipeline ──────────────────────────────
    from ..agents.pipeline import EvaluationPipeline, build_eval_context

    profile = services.get_profile(session=db, profile_id=ps.profile_id)
    eval_ctx = build_eval_context(
        user_message=req.message,
        ai_reply=ai_reply["reply"],
        scene=scene,
        turn_index=next_index,
        session_id=session_id,
        profile=profile,
    )
    pipeline = EvaluationPipeline()
    eval_result = pipeline.run(db=db, user_turn_id=user_turn.id, ctx=eval_ctx)
    light_hints = eval_result.light_hints

    # ── Build response ──────────────────────────────────────
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

    return schemas.ConversationResponse(
        reply=ai_reply["reply"],
        intent=ai_reply.get("intent", ""),
        based_on_user_point=ai_reply.get("based_on_user_point", ""),
        next_goal=ai_reply.get("next_goal", ""),
        should_interrupt=ai_reply.get("should_interrupt", False),
        is_final=ai_reply.get("intent") == "close_session",
        user_turn=_to_read(user_turn),
        ai_turn=_to_read(ai_turn),
        light_hints=light_hints,
        evaluation={
            "grammar": eval_result.grammar.model_dump(),
            "expression": eval_result.expression.model_dump(),
            "naturalness": eval_result.naturalness.model_dump(),
            "task_completion": eval_result.task_completion.model_dump(),
            "profile": eval_result.profile.model_dump(),
        },
    )


# ── Finish session ─────────────────────────────────────────────

@router.post("/{session_id}/finish", response_model=schemas.PracticeSessionRead)
def finish_session(session_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    """Mark a practice session as completed."""
    import datetime as _dt

    ps = services.get_session(session=db, session_id=session_id)
    if not ps:
        raise HTTPException(status_code=404, detail="PracticeSession not found")

    ps.status = "completed"
    ps.completed_at = _dt.datetime.now(_dt.timezone.utc)
    ps.updated_at = _dt.datetime.now(_dt.timezone.utc)
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return ps
