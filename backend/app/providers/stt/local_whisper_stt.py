"""Local Whisper STT provider — runs inference on-device, no API key or ffmpeg needed.

Uses faster-whisper (CTranslate2 backend) with tiny.en model.
- First run: downloads ~150MB model
- Inference: ~1-3 seconds on CPU for short utterances
- No ffmpeg required

Install: pip install faster-whisper
"""

from __future__ import annotations

import logging
import os
import tempfile

import numpy as np

from .base import BaseSTTProvider

logger = logging.getLogger("scenetalk.stt.local_whisper")

# Module-level singleton — loaded once, reused across all requests
_model = None
_model_name = os.getenv("WHISPER_MODEL", "tiny.en")


def _get_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError:
            raise RuntimeError(
                "faster-whisper 未安装。请运行: pip install faster-whisper"
            )
        logger.info(
            "Loading faster-whisper model: %s (~150MB, one-time)...",
            _model_name,
        )
        _model = WhisperModel(_model_name, device="cpu", compute_type="int8")
        logger.info("faster-whisper model ready.")
    return _model


class LocalWhisperSTTProvider(BaseSTTProvider):
    """Local Whisper speech-to-text using faster-whisper (CTranslate2).

    No API key required. No ffmpeg required. Model is a singleton — loaded once.
    Transcription latency: ~3-6 seconds on CPU for short utterances.
    """

    def __init__(self) -> None:
        pass  # model is a module-level singleton

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        model = _get_model()
        suffix = self._suffix_from_mime(mime_type)
        with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            segments, info = model.transcribe(
                tmp_path,
                language="en",
                beam_size=5,
                vad_filter=False,
            )
            transcript = " ".join(seg.text.strip() for seg in segments)
            logger.debug(
                "faster-whisper: %r (lang=%s prob=%.2f)",
                transcript,
                info.language,
                info.language_probability,
            )
            return transcript.strip()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @staticmethod
    def _suffix_from_mime(mime: str) -> str:
        return {
            "audio/wav": "wav",
            "audio/webm": "webm",
            "audio/mp3": "mp3",
            "audio/mpeg": "mp3",
            "audio/ogg": "ogg",
            "audio/flac": "flac",
        }.get(mime, "wav")
