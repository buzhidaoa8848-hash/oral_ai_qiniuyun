"""OpenAI Whisper STT provider — accepts direct file uploads (multipart).

OpenAI Whisper API supports direct audio file uploads, making it the
recommended provider for real-time voice recognition without additional
cloud storage infrastructure.
"""

import logging
import os
from io import BytesIO

from .base import BaseSTTProvider

logger = logging.getLogger("scenetalk.stt.openai")


class OpenaiSTTProvider(BaseSTTProvider):
    """OpenAI Whisper speech-to-text via direct file upload.

    Requires OPENAI_API_KEY in env.
    Supports: wav, webm, mp3, mp4, m4a, ogg, flac.
    """

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY 未设置，请在 .env 中配置")

        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise RuntimeError("openai 包未安装。请运行: pip install openai")

        client = OpenAI(api_key=self.api_key)

        # Map MIME type to file extension Whisper expects
        ext = self._ext_from_mime(mime_type)

        audio_file = BytesIO(audio_bytes)
        audio_file.name = f"recording.{ext}"

        logger.debug("Sending %d bytes to Whisper (as %s)", len(audio_bytes), audio_file.name)
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",  # English practice — adjust if needed
            response_format="text",
        )
        transcript = result.text if isinstance(result, dict) else str(result)
        return transcript.strip()

    @staticmethod
    def _ext_from_mime(mime: str) -> str:
        return {
            "audio/wav": "wav",
            "audio/wave": "wav",
            "audio/x-wav": "wav",
            "audio/webm": "webm",
            "audio/mp3": "mp3",
            "audio/mpeg": "mp3",
            "audio/mp4": "m4a",
            "audio/ogg": "ogg",
            "audio/flac": "flac",
        }.get(mime, "wav")
