"""Abstract base for STT providers."""

from abc import ABC, abstractmethod


class BaseSTTProvider(ABC):
    """Transcribe audio bytes to text."""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        """Return the transcribed text from the given audio data."""
        ...
