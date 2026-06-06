"""SQLModel table definitions for SceneTalk AI.

All models use:
- UUID4 primary keys (compatible with SQLite and PostgreSQL via SA Uuid type).
- created_at / updated_at timestamps.
- One-to-many relationships use typing.List with string forward references.
- Nullable relationships use typing.Optional.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import JSON, Column
from sqlalchemy.types import Uuid
from sqlmodel import Field, Relationship, SQLModel


def _newid() -> uuid.UUID:
    return uuid.uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════

class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    name: str = Field(max_length=128)
    email: Optional[str] = Field(default=None, max_length=256, index=True)
    source_language: str = Field(default="en", max_length=8)
    target_language: str = Field(default="zh", max_length=8)
    proficiency_level: str = Field(default="A1", max_length=4)
    # ── Personal profile fields ─────────────────────────────
    identity: Optional[str] = Field(default=None)
    experiences: Optional[str] = Field(default=None)
    strengths: Optional[str] = Field(default=None)
    thinking_style: Optional[str] = Field(default=None)
    target_role: Optional[str] = Field(default=None)
    expression_goal: Optional[str] = Field(default=None)
    # ── Learner profile fields ──────────────────────────────
    learner_identity: Optional[str] = Field(default=None)         # primary_school | middle_school | high_school | college | working_professional
    cefr_level: Optional[str] = Field(default="B1", max_length=4)  # A1-C2
    ielts_score: Optional[float] = Field(default=None)
    toefl_score: Optional[float] = Field(default=None)
    cet4_score: Optional[float] = Field(default=None)
    cet6_score: Optional[float] = Field(default=None)
    gaokao_english_score: Optional[float] = Field(default=None)
    zhongkao_english_score: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    sessions: List["PracticeSession"] = Relationship(back_populates="profile")
    reports: List["PersonalExpressionReport"] = Relationship(back_populates="profile")


# ═══════════════════════════════════════════════════════════════
# Material
# ═══════════════════════════════════════════════════════════════

class Material(SQLModel, table=True):
    __tablename__ = "materials"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    title: str = Field(max_length=256)
    content: str = Field(default="")                         # legacy / summary
    material_type: str = Field(default="text", max_length=64)
    language: str = Field(default="zh", max_length=8)
    # ── New fields ─────────────────────────────────────────
    raw_text: str = Field(default="")                        # full original text
    source_type: str = Field(default="paste", max_length=32)  # paste | txt | md | srt | vtt
    metadata_json: Optional[str] = Field(default=None)       # arbitrary JSON blob
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    scene_cards: List["SceneCard"] = Relationship(back_populates="material")


# ═══════════════════════════════════════════════════════════════
# SceneCard
# ═══════════════════════════════════════════════════════════════

class SceneCard(SQLModel, table=True):
    __tablename__ = "scene_cards"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    title: str = Field(max_length=256)
    difficulty: str = Field(max_length=4)
    topic: str = Field(max_length=64)
    # ── New scene-definition fields ─────────────────────────
    scene_type: str = Field(default="conversation", max_length=32)  # interview | restaurant | meeting | pitch
    style: str = Field(default="casual", max_length=32)             # professional | casual | semi-formal
    ai_role: str = Field(default="AI Assistant", max_length=128)    # who the AI plays
    user_role: str = Field(default="User", max_length=128)          # who the user plays
    task_goal: str = Field(default="")
    key_expressions: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    must_cover_points: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    follow_up_strategy: str = Field(default="")
    evaluation_rubric: str = Field(default="")
    opening_question: str = Field(default="")
    # ── Legacy / supplementary ────────────────────────────
    prompt: str = Field(default="")
    character_role: str = Field(default="", max_length=64)
    model_answer: str = Field(default="")
    hints: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    target_language: str = Field(default="zh", max_length=8)
    source_language: str = Field(default="en", max_length=8)
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    material_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="materials.id")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    material: Optional["Material"] = Relationship(back_populates="scene_cards")
    sessions: List["PracticeSession"] = Relationship(back_populates="scene_card")


# ═══════════════════════════════════════════════════════════════
# PracticeSession
# ═══════════════════════════════════════════════════════════════

class PracticeSession(SQLModel, table=True):
    __tablename__ = "practice_sessions"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    profile_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="profiles.id", index=True)
    scene_card_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="scene_cards.id", index=True)
    status: str = Field(default="in_progress", max_length=32)
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    profile: "Profile" = Relationship(back_populates="sessions")
    scene_card: "SceneCard" = Relationship(back_populates="sessions")
    turns: List["ConversationTurn"] = Relationship(back_populates="session")
    latency_metrics: List["LatencyMetric"] = Relationship(back_populates="session")
    reports: List["PersonalExpressionReport"] = Relationship(back_populates="session")


# ═══════════════════════════════════════════════════════════════
# ConversationTurn
# ═══════════════════════════════════════════════════════════════

class ConversationTurn(SQLModel, table=True):
    __tablename__ = "conversation_turns"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    session_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="practice_sessions.id", index=True)
    turn_index: int = Field(default=0)
    # ── New conversation fields ──────────────────────────────
    role: str = Field(default="user", max_length=16)  # "user" | "ai"
    message: str = Field(default="")                   # the actual text
    intent: Optional[str] = Field(default=None)        # AI: what it's trying to do
    based_on_user_point: Optional[str] = Field(default=None)  # AI: which user point addressed
    next_goal: Optional[str] = Field(default=None)     # AI: what to accomplish next
    should_interrupt: bool = Field(default=False)      # AI: should it interrupt the user
    # ── Legacy ──────────────────────────────────────────────
    audio_url: Optional[str] = Field(default=None, max_length=2048)
    transcript: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    session: "PracticeSession" = Relationship(back_populates="turns")
    evaluation: Optional["EvaluationResult"] = Relationship(back_populates="turn")
    latency_metrics: List["LatencyMetric"] = Relationship(back_populates="turn")


# ═══════════════════════════════════════════════════════════════
# EvaluationResult
# ═══════════════════════════════════════════════════════════════

class EvaluationResult(SQLModel, table=True):
    __tablename__ = "evaluation_results"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    turn_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="conversation_turns.id", index=True, unique=True)
    # ── Multi-agent scores ──────────────────────────────────
    grammar_score: Optional[float] = Field(default=None)
    grammar_notes: Optional[str] = Field(default=None)
    expression_score: Optional[float] = Field(default=None)
    expression_notes: Optional[str] = Field(default=None)
    naturalness_score: Optional[float] = Field(default=None)
    naturalness_notes: Optional[str] = Field(default=None)
    task_completion_score: Optional[float] = Field(default=None)
    task_completion_notes: Optional[str] = Field(default=None)
    # ── Legacy ──────────────────────────────────────────────
    pronunciation_score: Optional[float] = Field(default=None)
    fluency_score: Optional[float] = Field(default=None)
    vocabulary_score: Optional[float] = Field(default=None)
    overall_score: Optional[float] = Field(default=None)
    phoneme_feedback: Optional[str] = Field(default=None)
    model_audio_url: Optional[str] = Field(default=None, max_length=2048)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    turn: "ConversationTurn" = Relationship(back_populates="evaluation")
    corrections: List["CorrectionItem"] = Relationship(back_populates="evaluation")


# ═══════════════════════════════════════════════════════════════
# CorrectionItem
# ═══════════════════════════════════════════════════════════════

class CorrectionItem(SQLModel, table=True):
    __tablename__ = "correction_items"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    evaluation_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="evaluation_results.id", index=True)
    error_text: str
    correction: str
    explanation: Optional[str] = Field(default=None)
    category: str = Field(max_length=32)      # grammar | expression | naturalness | task
    timing: str = Field(default="post_session", max_length=32)  # post_session | light_recast | clarification | scaffold | immediate_allowed
    severity: float = Field(default=0.0)       # 0.0 (cosmetic) – 1.0 (critical)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    evaluation: "EvaluationResult" = Relationship(back_populates="corrections")


# ═══════════════════════════════════════════════════════════════
# LatencyMetric
# ═══════════════════════════════════════════════════════════════

class LatencyMetric(SQLModel, table=True):
    __tablename__ = "latency_metrics"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    session_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="practice_sessions.id", index=True)
    turn_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="conversation_turns.id", index=True)
    provider: str = Field(max_length=32)
    capability: str = Field(max_length=32)
    duration_ms: int = Field(default=0)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    session: Optional["PracticeSession"] = Relationship(back_populates="latency_metrics")
    turn: Optional["ConversationTurn"] = Relationship(back_populates="latency_metrics")


# ═══════════════════════════════════════════════════════════════
# PersonalExpressionReport
# ═══════════════════════════════════════════════════════════════

class PersonalExpressionReport(SQLModel, table=True):
    __tablename__ = "personal_expression_reports"

    id: uuid.UUID = Field(default_factory=_newid, sa_type=Uuid, primary_key=True)
    profile_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="profiles.id", index=True)
    session_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="practice_sessions.id", index=True)
    report_type: str = Field(max_length=32)
    expression_count: int = Field(default=0)
    unique_vocabulary: Optional[str] = Field(default=None)
    accuracy_trend: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    generated_at: datetime = Field(default_factory=_utcnow)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    profile: "Profile" = Relationship(back_populates="reports")
    session: Optional["PracticeSession"] = Relationship(back_populates="reports")
