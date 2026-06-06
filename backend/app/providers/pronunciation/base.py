"""Abstract base for pronunciation evaluation providers."""

from abc import ABC, abstractmethod
from typing import Optional


class PronunciationResult:
    """Output schema shared by all providers."""

    def __init__(
        self,
        *,
        words_per_minute: float = 0.0,
        filler_word_count: int = 0,
        repeated_word_count: int = 0,
        transcript_length: int = 0,
        audio_duration_seconds: float = 0.0,
        fluency_score: float = 0.0,
        pronunciation_score: float = 0.0,
        phoneme_feedback: Optional[str] = None,
        provider_name: str = "fallback",
        is_estimated: bool = True,
    ):
        self.words_per_minute = words_per_minute
        self.filler_word_count = filler_word_count
        self.repeated_word_count = repeated_word_count
        self.transcript_length = transcript_length
        self.audio_duration_seconds = audio_duration_seconds
        self.fluency_score = fluency_score
        self.pronunciation_score = pronunciation_score
        self.phoneme_feedback = phoneme_feedback
        self.provider_name = provider_name
        self.is_estimated = is_estimated

    def to_dict(self) -> dict:
        return {
            "words_per_minute": self.words_per_minute,
            "filler_word_count": self.filler_word_count,
            "repeated_word_count": self.repeated_word_count,
            "transcript_length": self.transcript_length,
            "audio_duration_seconds": self.audio_duration_seconds,
            "fluency_score": self.fluency_score,
            "pronunciation_score": self.pronunciation_score,
            "phoneme_feedback": self.phoneme_feedback,
            "provider_name": self.provider_name,
            "is_estimated": self.is_estimated,
        }


class BasePronunciationProvider(ABC):
    """Evaluate pronunciation and fluency from audio + transcript."""

    @abstractmethod
    def evaluate(
        self, audio_bytes: bytes, transcript: str, audio_duration_seconds: float
    ) -> PronunciationResult:
        ...
