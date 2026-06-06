"""CorrectionPolicyAgent — decides *when* to surface each correction.

Rules (in priority order):
  - error does NOT affect understanding   → post_session
  - error slightly affects naturalness     → light_recast
  - error blocks task completion           → clarification
  - user is stuck (multiple errors)        → scaffold
  - strict_mode enabled                    → immediate_allowed
"""

from .schemas import CorrectionPolicyOutput, EvalContext


class CorrectionPolicyAgent:

    def evaluate(self, ctx: EvalContext, grammar_errors: list[dict[str, object]]) -> CorrectionPolicyOutput:
        """Assign timing to each grammar/expression error."""
        items: list[dict[str, object]] = []

        for err in grammar_errors:
            severity = float(err.get("severity", 0.5))
            category = str(err.get("category", "grammar"))
            error_text = str(err.get("error_text", ""))
            correction = str(err.get("correction", ""))
            explanation = str(err.get("explanation", ""))

            timing = self._classify(
                severity=severity,
                category=category,
                error_text=error_text,
                strict=ctx.strict_mode,
                error_count=len(grammar_errors),
            )

            items.append({
                "error_text": error_text,
                "correction": correction,
                "explanation": explanation,
                "category": category,
                "severity": severity,
                "timing": timing,
            })

        return CorrectionPolicyOutput(items=items)

    def _classify(
        self,
        *,
        severity: float,
        category: str,
        error_text: str,
        strict: bool,
        error_count: int,
    ) -> str:
        if strict:
            return "immediate_allowed"

        # Critical errors block understanding
        if severity >= 0.8 or category == "task":
            return "clarification"

        # User might be stuck
        if error_count >= 4:
            return "scaffold"

        # Slight unnaturalness
        if severity >= 0.4:
            return "light_recast"

        # Cosmetic
        return "post_session"
