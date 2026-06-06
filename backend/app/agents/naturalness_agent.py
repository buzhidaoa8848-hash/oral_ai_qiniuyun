"""NaturalnessAgent — evaluates how natural the user's speech sounds."""

from .schemas import NaturalnessOutput, EvalContext

_FALLBACK = NaturalnessOutput(score=100.0, notes="Sounds natural.", flags=[])

# ── Mock checks ───────────────────────────────────────────────

_ROBOTIC_PATTERNS = [
    ("i would like to", "Consider a more casual alternative like 'I'd like to'."),
    ("it is my opinion that", "Overly formal — simplify to 'I think' or 'In my view'."),
    ("i am going to", "Try the contraction 'I'm gonna' for casual scenes."),
    ("i have a question regarding", "Simplify to 'I have a question about'."),
    ("i would appreciate it if", "Too formal for casual conversation. Try 'It'd be great if'."),
]


class NaturalnessAgent:

    def evaluate(self, ctx: EvalContext) -> NaturalnessOutput:
        text = ctx.user_message.lower()
        score = 100.0
        flags: list[str] = []
        notes: list[str] = []

        # ── Robotic phrasing (only flagged in casual scenes) ─
        if ctx.scene_type in ("restaurant", "conversation"):
            for pattern, suggestion in _ROBOTIC_PATTERNS:
                if pattern.lower() in text:
                    score -= 10.0
                    flags.append(suggestion)
                    notes.append(f"Robotic phrase: '{pattern}'.")

        # ── Lack of contractions (casual scenes) ─────────────
        if ctx.scene_type in ("restaurant", "conversation"):
            contraction_pairs = [
                ("i am", "I'm"), ("you are", "you're"), ("it is", "it's"),
                ("that is", "that's"), ("do not", "don't"), ("cannot", "can't"),
            ]
            formal_count = sum(1 for full, _short in contraction_pairs if full in text)
            if formal_count >= 3:
                score -= 10.0
                flags.append("Use more contractions for a natural, casual feel.")
                notes.append(f"Avoided {formal_count} common contractions.")

        score = max(0.0, min(100.0, score))

        if not notes:
            return _FALLBACK

        return NaturalnessOutput(
            score=round(score, 1),
            notes="; ".join(notes),
            flags=flags,
        )
