"""Multi-agent evaluation pipeline for SceneTalk AI.

Agents:
- CorrectionPolicyAgent — decides when to surface corrections
- GrammarAgent — detects grammar errors
- ExpressionAgent — evaluates expression quality
- PersonalProfileAgent — tracks user patterns over time
- NaturalnessAgent — evaluates conversational naturalness
- TaskCompletionAgent — checks task coverage
- ReportAgent — placeholder for post-session reporting
"""

from .pipeline import EvaluationPipeline

__all__ = ["EvaluationPipeline"]
