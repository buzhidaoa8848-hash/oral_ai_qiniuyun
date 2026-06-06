"""StyleAgent — enforces style constraints on AI conversation replies.

Ensures:
- Max 3 sentences (short spoken replies)
- Must end with a clear question (unless finishing)
- Matches scene style (casual / semi-formal / professional)
"""

from __future__ import annotations

from typing import Any


class StyleConstraints:
    """Immutable style rules derived from a SceneCard."""

    def __init__(self, scene: dict[str, Any]) -> None:
        self.style: str = scene.get("style", "casual")
        self.scene_type: str = scene.get("scene_type", "conversation")
        self.user_level: str = scene.get("difficulty", "B1")


class StyleAgent:
    """Validates and adjusts AI replies to conform to style constraints."""

    def enforce(self, reply: str, constraints: StyleConstraints, turn_count: int, is_final: bool = False) -> str:
        """Return a style-compliant version of `reply`.

        Rules:
        1. Trim to max 3 sentences.
        2. If not final, ensure last sentence is a question.
        3. Tone adjustments per style.
        """
        reply = reply.strip()

        # ── Rule 1: max 3 sentences ──────────────────────────
        sentences = _split_sentences(reply)
        if len(sentences) > 3:
            sentences = sentences[:3]
            reply = " ".join(sentences)

        # ── Rule 2: end with question (unless final) ─────────
        if not is_final and sentences:
            last = sentences[-1].strip()
            if not last.endswith("?"):
                # Append a natural follow-up question
                follow_ups = {
                    "casual": [
                        "What do you think?",
                        "How about you?",
                        "Does that sound right?",
                    ],
                    "professional": [
                        "What are your thoughts on this?",
                        "Could you share your perspective?",
                        "How does that align with your view?",
                    ],
                    "semi-formal": [
                        "What's your take?",
                        "How does that sound to you?",
                        "Would you agree?",
                    ],
                }
                options = follow_ups.get(constraints.style, follow_ups["casual"])
                # Pick a question not already in the reply
                for q in options:
                    if q.lower() not in reply.lower():
                        reply = reply.rstrip(".") + ". " + q
                        break
                else:
                    reply = reply.rstrip(".") + ". " + options[0]

        # ── Rule 3: tone adjustments ─────────────────────────
        if constraints.style == "professional" and turn_count == 0:
            # Opening should be polite and structured
            if not any(reply.lower().startswith(w) for w in ("good", "hello", "hi", "welcome", "thanks")):
                reply = "Hello! " + reply

        return reply.strip()

    def should_end_conversation(self, turn_count: int, user_said_goodbye: bool, all_points_covered: bool) -> bool:
        """Determine if the conversation should end."""
        if user_said_goodbye:
            return True
        if all_points_covered and turn_count >= 3:
            return True
        if turn_count >= 10:
            return True
        return False

    def closing_message(self, constraints: StyleConstraints) -> str:
        """Return a natural closing message."""
        closings = {
            "casual": "Great talking with you! Let's practice again soon — you did really well.",
            "professional": "Thank you for the productive conversation. Your responses were clear and well-structured.",
            "semi-formal": "This was a great session. I appreciate your thoughtful answers — well done.",
        }
        return closings.get(constraints.style, closings["casual"])


def _split_sentences(text: str) -> list[str]:
    """Naive sentence splitter for spoken English."""
    import re

    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p for p in parts if p.strip()]
