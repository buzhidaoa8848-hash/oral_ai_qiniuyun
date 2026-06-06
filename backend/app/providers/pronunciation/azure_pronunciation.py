"""Azure Speech pronunciation evaluation provider.

Uses Azure Pronunciation Assessment for real acoustic analysis:
- AccuracyScore, FluencyScore, CompletenessScore, PronScore
- Per-word and per-phoneme feedback

Requires: pip install azure-cognitiveservices-speech
Requires: AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in .env
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from .base import BasePronunciationProvider, PronunciationResult


class AzurePronunciationProvider(BasePronunciationProvider):
    """Real acoustic pronunciation analysis via Azure Cognitive Services."""

    def __init__(self, key: str = "", region: str = "") -> None:
        self.key = key or os.getenv("AZURE_SPEECH_KEY", "")
        self.region = region or os.getenv("AZURE_SPEECH_REGION", "")

    def evaluate(
        self,
        audio_bytes: bytes,
        transcript: str,
        audio_duration_seconds: float,
    ) -> PronunciationResult:
        if not self.key or not self.region:
            raise RuntimeError(
                "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set. "
                "Set pronunciation_provider=fallback to use the local estimator."
            )

        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            raise RuntimeError(
                "azure-cognitiveservices-speech not installed. "
                "Run: pip install azure-cognitiveservices-speech"
            )

        # ── Write audio to temp file (SDK needs a file or stream) ─
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.key, region=self.region
            )

            # Pronunciation assessment config
            pron_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=transcript,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            )
            pron_config.enable_prosody_assessment()

            # Use the temp file as audio input
            audio_config = speechsdk.audio.AudioConfig(filename=tmp_path)

            # Create recognizer
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                language="en-US",
                audio_config=audio_config,
            )
            pron_config.apply_to(recognizer)

            # Recognize
            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                raise RuntimeError(
                    f"Azure STT canceled: {cancellation.reason} — {cancellation.error_details}"
                )

            # ── Parse pronunciation assessment result ─────────
            pron_result = speechsdk.PronunciationAssessmentResult(result)
            accuracy = pron_result.accuracy_score
            fluency = pron_result.fluency_score
            completeness = pron_result.completeness_score
            pron_score = pron_result.pronunciation_score
            prosody = getattr(pron_result, "prosody_score", None)

            # Per-word feedback
            words_feedback: list[str] = []
            detail = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult
            )
            if detail:
                try:
                    parsed = json.loads(detail)
                    words = (
                        parsed.get("NBest", [{}])[0]
                        .get("Words", [])
                    )
                    for w in words:
                        w_score = w.get("PronunciationAssessment", {}).get(
                            "AccuracyScore", 0
                        )
                        if w_score < 80:
                            words_feedback.append(
                                f"{w.get('Word','?')}: {w_score:.0f}"
                            )
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

            phoneme_feedback_parts: list[str] = []
            phoneme_feedback_parts.append(
                f"Accuracy={accuracy:.0f} Fluency={fluency:.0f} "
                f"Completeness={completeness:.0f} Pron={pron_score:.0f}"
            )
            if prosody is not None:
                phoneme_feedback_parts.append(f"Prosody={prosody:.0f}")
            if words_feedback:
                phoneme_feedback_parts.append(
                    f"Words to improve: {'; '.join(words_feedback[:6])}"
                )

            return PronunciationResult(
                words_per_minute=0.0,
                filler_word_count=0,
                repeated_word_count=0,
                transcript_length=len(transcript.split()),
                audio_duration_seconds=audio_duration_seconds,
                fluency_score=round(fluency, 1),
                pronunciation_score=round(pron_score, 1),
                phoneme_feedback=" | ".join(phoneme_feedback_parts),
                provider_name="azure",
                is_estimated=False,
            )

        finally:
            os.unlink(tmp_path)
