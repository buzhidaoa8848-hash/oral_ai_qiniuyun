"""ExpressionAgent — evaluates vocabulary richness and expression quality."""

from .schemas import ExpressionOutput, EvalContext

_FALLBACK = ExpressionOutput(
    score=100.0,
    notes="Expression looks good.",
    suggestions=[],
)

# ── Mock checks ───────────────────────────────────────────────

_MIN_LENGTHS = {"A1": 3, "A2": 5, "B1": 8, "B2": 12, "C1": 15, "C2": 20}
_SIMPLE_WORDS = {"good", "bad", "nice", "big", "small", "thing", "stuff", "ok", "fine", "cool", "pretty"}
_WEAK_OPENERS = {"i think", "maybe", "i guess", "kind of", "sort of", "like"}


class ExpressionAgent:

    def evaluate(self, ctx: EvalContext) -> ExpressionOutput:
        text = ctx.user_message
        words = text.lower().split()
        score = 100.0
        notes: list[str] = []
        suggestions: list[str] = []

        # ── Length check ─────────────────────────────────────
        min_len = _MIN_LENGTHS.get(ctx.user_level, 5)
        if len(words) < min_len:
            score -= 15.0
            suggestions.append(f"Try using at least {min_len} words for {ctx.user_level} level.")
            notes.append("Reply is quite short for this level.")

        # ── Vocabulary diversity ─────────────────────────────
        unique = {w for w in words if len(w) > 2}
        simple_count = sum(1 for w in unique if w in _SIMPLE_WORDS)
        if simple_count >= 3:
            score -= 10.0
            suggestions.append("Consider using more specific vocabulary instead of generic words like 'good' or 'nice'.")
            notes.append(f"Found {simple_count} overly simple word(s).")

        # ── Weak openers ─────────────────────────────────────
        lower_text = text.lower()
        weak_found = [w for w in _WEAK_OPENERS if lower_text.startswith(w)]
        if weak_found:
            score -= 10.0
            suggestions.append("Start with a more confident opener instead of hedging phrases.")
            notes.append(f"Hedging opener: '{weak_found[0]}'.")

        # ── Repetition ───────────────────────────────────────
        if len(words) >= 6:
            word_counts: dict[str, int] = {}
            for w in words:
                if len(w) > 3:
                    word_counts[w] = word_counts.get(w, 0) + 1
            repeated = [w for w, c in word_counts.items() if c >= 3]
            if repeated:
                score -= 5.0
                suggestions.append("Avoid repeating the same words. Try synonyms.")
                notes.append(f"Repeated word(s): {', '.join(repeated[:3])}.")

        score = max(0.0, min(100.0, score))

        if not notes:
            return _FALLBACK

        return ExpressionOutput(
            score=round(score, 1),
            notes="; ".join(notes),
            suggestions=suggestions,
        )
