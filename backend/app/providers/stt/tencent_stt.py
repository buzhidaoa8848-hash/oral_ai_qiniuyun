"""Tencent Cloud STT provider (placeholder)."""

import os
from .base import BaseSTTProvider


class TencentSTTProvider(BaseSTTProvider):
    def __init__(self) -> None:
        pass

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        raise NotImplementedError(
            "Tencent Cloud STT is not yet implemented. "
            "Set STT_PROVIDER=mock or use openai."
        )
