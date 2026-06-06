"""EvaluationPipeline — runs all agents after each turn and persists results.

TODO: Move this to an async task queue (Redis/RQ or Celery) for production.
      Currently runs inline — fine for mock mode, will add latency with real LLMs.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlmodel import Session

from .. import models as m
from .schemas import (
    EvalContext,
    EvalPipelineResult,
    GrammarOutput,
    ExpressionOutput,
    NaturalnessOutput,
    TaskCompletionOutput,
    ProfileOutput,
)
from .correction_policy import CorrectionPolicyAgent
from .grammar_agent import GrammarAgent
from .expression_agent import ExpressionAgent
from .profile_agent import PersonalProfileAgent
from .naturalness_agent import NaturalnessAgent
from .task_completion import TaskCompletionAgent


class EvaluationPipeline:
    """Run all agents, persist EvaluationResult + CorrectionItems, return light hints."""

    def __init__(self) -> None:
        self.grammar = GrammarAgent()
        self.expression = ExpressionAgent()
        self.naturalness = NaturalnessAgent()
        self.task_completion = TaskCompletionAgent()
        self.profile = PersonalProfileAgent()
        self.policy = CorrectionPolicyAgent()

    def run(
        self,
        *,
        db: Session,
        user_turn_id: uuid.UUID,
        ctx: EvalContext,
        pronunciation_score: float | None = None,
        fluency_score: float | None = None,
        phoneme_feedback: str | None = None,
        is_pron_estimated: bool = True,
    ) -> EvalPipelineResult:
        """Execute all agents, persist results, return pipeline output."""

        # ── 1. Run agents ────────────────────────────────────
        grammar_out = self.grammar.evaluate(ctx)
        expression_out = self.expression.evaluate(ctx)
        naturalness_out = self.naturalness.evaluate(ctx)
        task_out = self.task_completion.evaluate(ctx)
        profile_out = self.profile.evaluate(ctx, profile=ctx.profile)

        # ── 2. Correction policy ─────────────────────────────
        # Collect all errors from grammar + expression
        all_errors: list[dict[str, object]] = []
        for err in grammar_out.errors:
            all_errors.append(dict(err))
        # Expression suggestions → convert to error format
        for sug in expression_out.suggestions:
            all_errors.append({
                "error_text": sug,
                "correction": "",
                "explanation": sug,
                "category": "expression",
                "severity": 0.3,
            })

        correction_out = self.policy.evaluate(ctx, all_errors)

        # ── 3. Compute overall score ─────────────────────────
        scores = [
            grammar_out.score,
            expression_out.score,
            naturalness_out.score,
            task_out.score,
        ]
        overall = round(sum(scores) / len(scores), 1)

        # ── 4. Persist EvaluationResult ──────────────────────
        eval_result = m.EvaluationResult(
            turn_id=user_turn_id,
            grammar_score=grammar_out.score,
            grammar_notes=grammar_out.notes,
            expression_score=expression_out.score,
            expression_notes=expression_out.notes,
            naturalness_score=naturalness_out.score,
            naturalness_notes=naturalness_out.notes,
            task_completion_score=task_out.score,
            task_completion_notes=task_out.notes,
            pronunciation_score=pronunciation_score,
            fluency_score=fluency_score,
            phoneme_feedback=phoneme_feedback,
            overall_score=overall,
        )
        db.add(eval_result)
        db.flush()  # get eval_result.id for correction items

        # ── 5. Persist CorrectionItems ───────────────────────
        light_hints: list[str] = []
        for item in correction_out.items:
            timing = str(item.get("timing", "post_session"))
            ci = m.CorrectionItem(
                evaluation_id=eval_result.id,
                error_text=str(item.get("error_text", "")),
                correction=str(item.get("correction", "")),
                explanation=str(item.get("explanation", "")),
                category=str(item.get("category", "grammar")),
                timing=timing,
                severity=float(item.get("severity", 0.0)),
            )
            db.add(ci)

            # light hints: only show light_recast items to the user
            if timing in ("light_recast", "clarification"):
                light_hints.append(str(item.get("correction", item.get("explanation", ""))))

        db.commit()

        # ── 6. Return result ─────────────────────────────────
        return EvalPipelineResult(
            grammar=grammar_out,
            expression=expression_out,
            naturalness=naturalness_out,
            task_completion=task_out,
            profile=profile_out,
            corrections=[dict(it) for it in correction_out.items],
            light_hints=light_hints,
        )


def build_eval_context(
    *,
    user_message: str,
    ai_reply: str,
    scene: m.SceneCard,
    turn_index: int,
    session_id: uuid.UUID,
    profile: m.Profile | None = None,
) -> EvalContext:
    """Build the EvalContext from live objects."""
    profile_dict: dict[str, str] = {}
    if profile:
        profile_dict = {
            "identity": profile.identity or "",
            "experiences": profile.experiences or "",
            "strengths": profile.strengths or "",
            "thinking_style": profile.thinking_style or "",
            "target_role": profile.target_role or "",
            "expression_goal": profile.expression_goal or "",
        }
    return EvalContext(
        user_message=user_message,
        ai_reply=ai_reply,
        scene_title=scene.title,
        scene_type=scene.scene_type,
        task_goal=scene.task_goal,
        must_cover_points=scene.must_cover_points or [],
        user_level=scene.difficulty,
        turn_index=turn_index,
        session_id=str(session_id),
        strict_mode=False,
        profile=profile_dict,
    )
