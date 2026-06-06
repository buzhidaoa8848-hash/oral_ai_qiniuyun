"""TaskCompletionAgent — checks which must-cover points have been addressed."""

from .schemas import TaskCompletionOutput, EvalContext

_FALLBACK = TaskCompletionOutput(
    score=100.0,
    covered_points=[],
    missing_points=[],
    notes="No must-cover points defined for this scene.",
)


class TaskCompletionAgent:

    def evaluate(self, ctx: EvalContext) -> TaskCompletionOutput:
        if not ctx.must_cover_points:
            return _FALLBACK

        text = ctx.user_message.lower()
        covered: list[str] = []
        missing: list[str] = []

        for point in ctx.must_cover_points:
            # Simple keyword matching — extract key words from the point
            keywords = [w for w in point.lower().split() if len(w) > 3][:3]
            if not keywords:
                keywords = point.lower().split()[:2]
            if any(kw in text for kw in keywords):
                covered.append(point)
            else:
                missing.append(point)

        total = len(ctx.must_cover_points)
        score = (len(covered) / total) * 100.0 if total > 0 else 100.0

        return TaskCompletionOutput(
            score=round(score, 1),
            covered_points=covered,
            missing_points=missing,
            notes=f"Covered {len(covered)}/{total} required points." if covered else "No points covered yet.",
        )
