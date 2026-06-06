"""OpenAI Whisper STT provider (placeholder — requires openai package)."""

import os
from .base import BaseSTTProvider


class OpenaiSTTProvider(BaseSTTProvider):
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed")

        client = OpenAI(api_key=self.api_key)
        # OpenAI expects a file-like object; wrap bytes
        from io import BytesIO

        audio_file = BytesIO(audio_bytes)
        audio_file.name = "recording.webm"

        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        return result.text
