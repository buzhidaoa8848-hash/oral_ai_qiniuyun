"""ReportAgent — generates a comprehensive post-session report.

Aggregates all evaluation results, correction items, latency metrics,
and profile data into a structured report.
"""

from __future__ import annotations

import uuid
from collections import Counter
from typing import Any

from sqlmodel import Session, select

from .. import models as m


class ReportAgent:

    def generate(self, *, db: Session, session_id: uuid.UUID) -> dict[str, Any]:
        """Build the full session report dict."""
        # ── Load data ────────────────────────────────────────
        ps = db.get(m.PracticeSession, session_id)
        if not ps:
            raise ValueError(f"Session {session_id} not found")

        scene = db.get(m.SceneCard, ps.scene_card_id)
        profile = db.get(m.Profile, ps.profile_id)

        turns = db.exec(
            select(m.ConversationTurn)
            .where(m.ConversationTurn.session_id == session_id)
            .order_by(m.ConversationTurn.turn_index)
        ).all()

        evaluations = db.exec(
            select(m.EvaluationResult)
            .where(m.EvaluationResult.turn_id.in_([t.id for t in turns if t.role == "user"]))
        ).all()

        corrections = db.exec(
            select(m.CorrectionItem)
            .where(m.CorrectionItem.evaluation_id.in_([e.id for e in evaluations]))
        ).all()

        latencies = db.exec(
            select(m.LatencyMetric)
            .where(m.LatencyMetric.session_id == session_id)
        ).all()

        # ── Aggregate scores ──────────────────────────────────
        scores = self._aggregate_scores(evaluations)
        correction_timing = self._timing_summary(corrections)
        latency_summary = self._latency_summary(latencies)
        top_issues = self._top_issues(corrections)
        profile_report = self._profile_report(evaluations, profile)
        if_i_were_you = self._generate_if_i_were_you(profile_report, scene, turns)
        next_plan = self._next_plan(scores, top_issues, profile)

        user_turns = [t for t in turns if t.role == "user"]

        return {
            "session_id": str(session_id),
            "status": ps.status,
            "scene_title": scene.title if scene else "Unknown",
            "scene_type": scene.scene_type if scene else "",
            "turn_count": len(user_turns),
            "started_at": ps.started_at.isoformat() if ps.started_at else None,
            "completed_at": ps.completed_at.isoformat() if ps.completed_at else None,
            # ── Scores ───────────────────────────────────────
            "overall_score": scores["overall"],
            "pronunciation": scores["pronunciation"],
            "fluency": scores["fluency"],
            "grammar": scores["grammar"],
            "expression": scores["expression"],
            "task_completion": scores["task_completion"],
            "self_expression": scores["self_expression"],
            "naturalness": scores["naturalness"],
            # ── Details ──────────────────────────────────────
            "latency_summary": latency_summary,
            "correction_timing_summary": correction_timing,
            "top_issues": top_issues,
            "if_i_were_you": if_i_were_you,
            "next_practice_plan": next_plan,
        }

    # ── Aggregation helpers ──────────────────────────────────

    def _aggregate_scores(self, evaluations: list[m.EvaluationResult]) -> dict[str, float]:
        if not evaluations:
            return {
                "overall": 0, "pronunciation": 0, "fluency": 0,
                "grammar": 0, "expression": 0, "task_completion": 0,
                "self_expression": 0, "naturalness": 0,
            }

        def _avg(getter):
            vals = [getter(e) for e in evaluations if getter(e) is not None]
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        return {
            "overall": _avg(lambda e: e.overall_score),
            "pronunciation": _avg(lambda e: e.pronunciation_score),
            "fluency": _avg(lambda e: e.fluency_score),
            "grammar": _avg(lambda e: e.grammar_score),
            "expression": _avg(lambda e: e.expression_score),
            "task_completion": _avg(lambda e: e.task_completion_score),
            "self_expression": _avg(lambda e: e.overall_score),  # approximate
            "naturalness": _avg(lambda e: e.naturalness_score),
        }

    def _timing_summary(self, corrections: list[m.CorrectionItem]) -> dict[str, int]:
        timing = Counter(c.timing for c in corrections)
        return {
            "post_session": timing.get("post_session", 0),
            "light_recast": timing.get("light_recast", 0),
            "clarification": timing.get("clarification", 0),
            "scaffold": timing.get("scaffold", 0),
            "immediate_allowed": timing.get("immediate_allowed", 0),
            "total": len(corrections),
        }

    def _latency_summary(self, latencies: list[m.LatencyMetric]) -> dict[str, Any]:
        by_capability: dict[str, list[int]] = {}
        for lm in latencies:
            by_capability.setdefault(lm.capability, []).append(lm.duration_ms)

        summary: dict[str, Any] = {"total_metrics": len(latencies)}
        for cap, vals in by_capability.items():
            summary[cap] = {
                "avg_ms": round(sum(vals) / len(vals), 1) if vals else 0,
                "min_ms": min(vals),
                "max_ms": max(vals),
                "count": len(vals),
            }

        e2e_vals = []
        for lm in latencies:
            if lm.capability in ("stt", "llm", "tts", "pronunciation"):
                e2e_vals.append(lm.duration_ms)
        summary["e2e_estimate_ms"] = sum(e2e_vals) if e2e_vals else 0
        return summary

    def _top_issues(self, corrections: list[m.CorrectionItem]) -> list[dict[str, Any]]:
        # Group by error text, take top 5
        grouped: dict[str, list[m.CorrectionItem]] = {}
        for c in corrections:
            grouped.setdefault(c.error_text, []).append(c)

        sorted_issues = sorted(grouped.items(), key=lambda x: -len(x[1]))[:5]
        return [
            {
                "error_text": error,
                "correction": items[0].correction,
                "category": items[0].category,
                "count": len(items),
                "timing": items[0].timing,
                "severity": round(max(it.severity for it in items), 2),
            }
            for error, items in sorted_issues
        ]

    def _profile_report(
        self, evaluations: list[m.EvaluationResult], profile: m.Profile | None
    ) -> dict[str, Any]:
        return {
            "identity": profile.identity if profile else None,
            "target_role": profile.target_role if profile else None,
            "expression_goal": profile.expression_goal if profile else None,
            "strengths": profile.strengths if profile else None,
            "eval_count": len(evaluations),
        }

    def _generate_if_i_were_you(
        self,
        profile_report: dict[str, Any],
        scene: m.SceneCard | None,
        turns: list[m.ConversationTurn],
    ) -> str:
        """Generate a personalized model-answer style suggestion."""
        parts: list[str] = []

        if scene:
            parts.append(f"For the '{scene.title}' scene, I'd approach it this way:")

        if profile_report.get("target_role"):
            parts.append(f"As a {profile_report['target_role']}, I'd highlight relevant experience right away.")

        if profile_report.get("strengths"):
            parts.append(f"I'd weave in my strengths ({profile_report['strengths']}) naturally through concrete examples.")

        user_msgs = [t.message for t in turns if t.role == "user"]
        avg_len = sum(len(m.split()) for m in user_msgs) / max(len(user_msgs), 1)
        if avg_len < 10:
            parts.append("I'd elaborate more — aim for 3-4 sentences with specific project details and data.")

        if scene and scene.opening_question:
            parts.append(f"When asked '{scene.opening_question[:60]}...', I'd structure my answer: (1) context, (2) my specific role, (3) concrete result, (4) what I learned.")

        if not parts:
            parts.append("I'd structure each answer with a clear STAR format: Situation, Task, Action, Result.")

        return " ".join(parts)

    def _next_plan(
        self,
        scores: dict[str, float],
        top_issues: list[dict[str, Any]],
        profile: m.Profile | None,
    ) -> dict[str, Any]:
        """Suggest the next practice focus."""
        # Find weakest area
        areas = [
            ("grammar", scores.get("grammar", 0)),
            ("expression", scores.get("expression", 0)),
            ("naturalness", scores.get("naturalness", 0)),
            ("task_completion", scores.get("task_completion", 0)),
            ("pronunciation", scores.get("pronunciation", 0)),
            ("fluency", scores.get("fluency", 0)),
        ]
        areas.sort(key=lambda x: x[1])
        weakest = areas[0]

        focus_scenes = {
            "grammar": "Try the 'Restaurant Ordering' scene for casual grammar practice.",
            "expression": "The 'Project Pitch Q&A' scene will push your vocabulary range.",
            "naturalness": "Practice 'Restaurant Ordering' with a focus on sounding relaxed.",
            "task_completion": "Work on 'Work Meeting' — it has clear structured goals.",
            "pronunciation": "Use voice mode with 'Internship Interview' for pronunciation reps.",
            "fluency": "Any scene in voice mode will build fluency through repetition.",
        }

        return {
            "weakest_area": weakest[0],
            "weakest_score": weakest[1],
            "suggested_scene": focus_scenes.get(weakest[0], "Keep practicing any scene."),
            "tip": "Focus on quality over quantity — 3 well-structured answers beat 10 rushed ones.",
            "expression_goal": profile.expression_goal if profile else None,
        }
