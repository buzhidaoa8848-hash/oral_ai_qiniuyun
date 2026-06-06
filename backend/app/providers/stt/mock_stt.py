"""Mock STT — returns deterministic transcripts based on turn count."""

import time
import random
from .base import BaseSTTProvider

_MOCK_TRANSCRIPTS = [
    "Hi there! I'm a CS student and I'm really interested in this internship opportunity.",
    "Last semester I built a full-stack web app for study group matching. I handled both the backend API and the deployment.",
    "The biggest challenge was handling real-time notifications across different time zones. I solved it with a message queue.",
    "I'd love to work here because your company really values developer experience, and that's something I'm passionate about.",
    "Yes, I do have a question — what does the onboarding process look like for interns?",
    "Thank you so much for your time today. I really appreciate the opportunity to speak with you.",
]

# Module-level counter so transcripts cycle across provider instances
_call_count = 0


class MockSTTProvider(BaseSTTProvider):
    """Returns canned transcripts — always succeeds and cycles through varied replies."""

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        global _call_count
        # Simulate STT latency (80-200ms)
        time.sleep(0.05 + random.random() * 0.15)
        idx = _call_count % len(_MOCK_TRANSCRIPTS)
        _call_count += 1
        return _MOCK_TRANSCRIPTS[idx]
