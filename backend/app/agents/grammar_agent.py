"""GrammarAgent — detects grammar errors in user utterance."""

from .schemas import GrammarOutput, EvalContext

# ── Simple rule-based grammar checks (mock mode) ──────────────

_RULES = [
    {
        "pattern": "i am",
        "check": lambda t: "i am" in t.lower() and not t.startswith("I am"),
        "error": "lowercase 'i' should be 'I'",
        "fix": "Capitalize 'I'",
        "severity": 0.2,
    },
    {
        "pattern": "he don't|she don't|it don't",
        "check": lambda t: any(p in t.lower() for p in ["he don't", "she don't", "it don't"]),
        "error": "'don't' should be 'doesn't' with he/she/it",
        "fix": "Use 'doesn't' instead of 'don't'",
        "severity": 0.5,
    },
    {
        "pattern": "more better|more worse|more faster",
        "check": lambda t: any(p in t.lower() for p in ["more better", "more worse", "more faster"]),
        "error": "Double comparative — 'more' + '-er'",
        "fix": "Use just 'better'/'worse'/'faster'",
        "severity": 0.4,
    },
    {
        "pattern": "yesterday i go|last week i go|yesterday i see",
        "check": lambda t: any(p in t.lower() for p in ["yesterday i go", "last week i go", "yesterday i see"]),
        "error": "Past tense needed for past time reference",
        "fix": "Use past tense (went/saw) with past time markers",
        "severity": 0.6,
    },
    {
        "pattern": "there is many|there is several|there is some people",
        "check": lambda t: any(p in t.lower() for p in ["there is many", "there is several", "there is some people"]),
        "error": "'There is' should be 'There are' with plural nouns",
        "fix": "Use 'There are' for plural subjects",
        "severity": 0.5,
    },
]

_FALLBACK = GrammarOutput(
    score=100.0,
    notes="No grammar errors detected.",
    errors=[],
)


class GrammarAgent:

    def evaluate(self, ctx: EvalContext) -> GrammarOutput:
        """Run grammar checks on the user's message."""
        text = ctx.user_message
        errors: list[dict[str, object]] = []
        total_penalty = 0.0

        for rule in _RULES:
            if rule["check"](text):
                errors.append({
                    "error_text": rule["error"],
                    "correction": rule["fix"],
                    "explanation": rule["error"],
                    "severity": rule["severity"],
                    "category": "grammar",
                })
                total_penalty += rule["severity"] * 15.0  # each severity point = 15% off

        score = max(0.0, min(100.0, 100.0 - total_penalty))

        if not errors:
            return _FALLBACK

        return GrammarOutput(
            score=round(score, 1),
            notes=f"Found {len(errors)} grammar issue(s).",
            errors=errors,
        )
