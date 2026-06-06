"""Typed Pydantic input/output schemas for all evaluation agents."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# Shared context passed to every agent
# ═══════════════════════════════════════════════════════════════

class EvalContext(BaseModel):
    """Immutable snapshot the pipeline passes to every agent."""
    user_message: str
    ai_reply: str
    scene_title: str = ""
    scene_type: str = "conversation"
    task_goal: str = ""
    must_cover_points: list[str] = Field(default_factory=list)
    user_level: str = "B1"
    turn_index: int = 0
    session_id: str = ""
    strict_mode: bool = False
    profile: dict[str, str] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# CorrectionPolicyAgent
# ═══════════════════════════════════════════════════════════════

class CorrectionPolicyOutput(BaseModel):
    items: list[dict[str, object]] = Field(default_factory=list)
    # Each item: {error_text, correction, explanation, category, severity, timing}


# ═══════════════════════════════════════════════════════════════
# GrammarAgent
# ═══════════════════════════════════════════════════════════════

class GrammarOutput(BaseModel):
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    notes: str = ""
    errors: list[dict[str, object]] = Field(default_factory=list)
    # Each error: {error_text, correction, explanation, severity}


# ═══════════════════════════════════════════════════════════════
# ExpressionAgent
# ═══════════════════════════════════════════════════════════════

class ExpressionOutput(BaseModel):
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    notes: str = ""
    suggestions: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# PersonalProfileAgent
# ═══════════════════════════════════════════════════════════════

class ProfileOutput(BaseModel):
    self_expression_score: float = Field(default=50.0, ge=0.0, le=100.0)
    profile_coverage: float = Field(default=0.0, ge=0.0, le=100.0)
    evidence_density: float = Field(default=0.0, ge=0.0, le=100.0)
    agency: float = Field(default=0.0, ge=0.0, le=100.0)
    original_thinking: float = Field(default=0.0, ge=0.0, le=100.0)
    position_fit: float = Field(default=0.0, ge=0.0, le=100.0)
    expressed_traits: list[str] = Field(default_factory=list)
    missing_traits: list[str] = Field(default_factory=list)
    if_i_were_you: str = ""
    # legacy
    patterns: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestion: str = ""


# ═══════════════════════════════════════════════════════════════
# NaturalnessAgent
# ═══════════════════════════════════════════════════════════════

class NaturalnessOutput(BaseModel):
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    notes: str = ""
    flags: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# TaskCompletionAgent
# ═══════════════════════════════════════════════════════════════

class TaskCompletionOutput(BaseModel):
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    covered_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    notes: str = ""


# ═══════════════════════════════════════════════════════════════
# ReportAgent
# ═══════════════════════════════════════════════════════════════

class ReportOutput(BaseModel):
    summary: str = ""
    scores: dict[str, float] = Field(default_factory=dict)
    top_strengths: list[str] = Field(default_factory=list)
    top_improvements: list[str] = Field(default_factory=list)
    recommendation: str = ""


# ═══════════════════════════════════════════════════════════════
# Aggregated pipeline result
# ═══════════════════════════════════════════════════════════════

class EvalPipelineResult(BaseModel):
    grammar: GrammarOutput
    expression: ExpressionOutput
    naturalness: NaturalnessOutput
    task_completion: TaskCompletionOutput
    profile: ProfileOutput
    corrections: list[dict[str, object]]  # from CorrectionPolicy
    light_hints: list[str] = Field(default_factory=list)  # for frontend display
