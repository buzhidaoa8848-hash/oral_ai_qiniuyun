"""Pydantic schemas for API request / response bodies.

Separated from models.py so the database layer and API layer can evolve independently.
Every model gets Create / Update / Read variants.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


# ── Profile ───────────────────────────────────────────────────

class ProfileCreate(SQLModel):
    name: str
    email: str | None = None
    source_language: str = "en"
    target_language: str = "zh"
    proficiency_level: str = "A1"
    identity: str | None = None
    experiences: str | None = None
    strengths: str | None = None
    thinking_style: str | None = None
    target_role: str | None = None
    expression_goal: str | None = None
    learner_identity: str | None = None
    cefr_level: str | None = "B1"
    ielts_score: float | None = None
    toefl_score: float | None = None
    cet4_score: float | None = None
    cet6_score: float | None = None
    gaokao_english_score: float | None = None
    zhongkao_english_score: float | None = None


class ProfileUpdate(SQLModel):
    name: str | None = None
    email: str | None = None
    source_language: str | None = None
    target_language: str | None = None
    proficiency_level: str | None = None
    identity: str | None = None
    experiences: str | None = None
    strengths: str | None = None
    thinking_style: str | None = None
    target_role: str | None = None
    expression_goal: str | None = None
    learner_identity: str | None = None
    cefr_level: str | None = None
    ielts_score: float | None = None
    toefl_score: float | None = None
    cet4_score: float | None = None
    cet6_score: float | None = None
    gaokao_english_score: float | None = None
    zhongkao_english_score: float | None = None


class ProfileRead(SQLModel):
    id: uuid.UUID
    name: str
    email: str | None = None
    source_language: str
    target_language: str
    proficiency_level: str
    identity: str | None = None
    experiences: str | None = None
    strengths: str | None = None
    thinking_style: str | None = None
    target_role: str | None = None
    expression_goal: str | None = None
    learner_identity: str | None = None
    cefr_level: str | None = None
    ielts_score: float | None = None
    toefl_score: float | None = None
    cet4_score: float | None = None
    cet6_score: float | None = None
    gaokao_english_score: float | None = None
    zhongkao_english_score: float | None = None
    created_at: datetime
    updated_at: datetime


# ── Material ──────────────────────────────────────────────────

class MaterialCreate(SQLModel):
    title: str
    content: str = ""
    material_type: str = "text"
    language: str = "zh"
    raw_text: str = ""
    source_type: str = "paste"
    metadata_json: str | None = None


class MaterialUpdate(SQLModel):
    title: str | None = None
    content: str | None = None
    material_type: str | None = None
    language: str | None = None
    raw_text: str | None = None
    source_type: str | None = None
    metadata_json: str | None = None


class MaterialRead(SQLModel):
    id: uuid.UUID
    title: str
    content: str
    material_type: str
    language: str
    raw_text: str
    source_type: str
    metadata_json: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Material paste / upload ──────────────────────────────────

class MaterialPasteIn(SQLModel):
    """Pasted text payload."""
    title: str
    raw_text: str
    source_type: str = "paste"
    language: str = "en"
    metadata_json: str | None = None


class SceneGenerateRequest(SQLModel):
    """Payload for the Scene Builder Agent (material_id comes from URL path)."""
    scene_type: str = "conversation"
    style: str = "casual"
    user_level: str = "B1"
    target_goal: str = ""


# ── SceneCard ─────────────────────────────────────────────────

class SceneCardCreate(SQLModel):
    title: str
    difficulty: str = "A1"
    topic: str
    # new fields
    scene_type: str = "conversation"
    style: str = "casual"
    ai_role: str = "AI Assistant"
    user_role: str = "User"
    task_goal: str = ""
    key_expressions: list[str] | None = None
    must_cover_points: list[str] | None = None
    follow_up_strategy: str = ""
    evaluation_rubric: str = ""
    opening_question: str = ""
    # legacy
    prompt: str = ""
    character_role: str = ""
    model_answer: str = ""
    hints: list[str] | None = None
    target_language: str = "zh"
    source_language: str = "en"
    tags: list[str] | None = None
    material_id: uuid.UUID | None = None


class SceneCardUpdate(SQLModel):
    title: str | None = None
    difficulty: str | None = None
    topic: str | None = None
    scene_type: str | None = None
    style: str | None = None
    ai_role: str | None = None
    user_role: str | None = None
    task_goal: str | None = None
    key_expressions: list[str] | None = None
    must_cover_points: list[str] | None = None
    follow_up_strategy: str | None = None
    evaluation_rubric: str | None = None
    opening_question: str | None = None
    prompt: str | None = None
    character_role: str | None = None
    model_answer: str | None = None
    hints: list[str] | None = None
    target_language: str | None = None
    source_language: str | None = None
    tags: list[str] | None = None
    material_id: uuid.UUID | None = None


class SceneCardRead(SQLModel):
    id: uuid.UUID
    title: str
    difficulty: str
    topic: str
    scene_type: str
    style: str
    ai_role: str
    user_role: str
    task_goal: str
    key_expressions: list[str] | None = None
    must_cover_points: list[str] | None = None
    follow_up_strategy: str
    evaluation_rubric: str
    opening_question: str
    prompt: str
    character_role: str
    model_answer: str
    hints: list[str] | None = None
    target_language: str
    source_language: str
    tags: list[str] | None = None
    material_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


# ── PracticeSession ───────────────────────────────────────────

class PracticeSessionCreate(SQLModel):
    profile_id: uuid.UUID
    scene_card_id: uuid.UUID
    status: str = "in_progress"


class PracticeSessionUpdate(SQLModel):
    status: str | None = None
    completed_at: datetime | None = None


class PracticeSessionRead(SQLModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    scene_card_id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ── Conversation ──────────────────────────────────────────────

class ConversationTurnRead(SQLModel):
    id: uuid.UUID
    session_id: uuid.UUID
    turn_index: int
    role: str
    message: str
    intent: str | None = None
    based_on_user_point: str | None = None
    next_goal: str | None = None
    should_interrupt: bool = False
    audio_url: str | None = None
    transcript: str | None = None
    created_at: datetime


class ConversationRequest(SQLModel):
    """User sends a message to the conversation."""
    message: str


class ConversationResponse(SQLModel):
    """AI reply + metadata."""
    reply: str
    intent: str
    based_on_user_point: str
    next_goal: str
    should_interrupt: bool
    is_final: bool = False
    user_turn: ConversationTurnRead
    ai_turn: ConversationTurnRead
    light_hints: list[str] = []
    evaluation: dict[str, object] = {}


# ── EvaluationResult (brief) ──────────────────────────────────

class EvaluationResultRead(SQLModel):
    id: uuid.UUID
    turn_id: uuid.UUID
    pronunciation_score: float | None = None
    fluency_score: float | None = None
    grammar_score: float | None = None
    vocabulary_score: float | None = None
    overall_score: float | None = None


# ── PersonalExpressionReport ──────────────────────────────────

class ReportCreate(SQLModel):
    profile_id: uuid.UUID
    session_id: uuid.UUID | None = None
    report_type: str = "session"


class ReportRead(SQLModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    session_id: uuid.UUID | None = None
    report_type: str
    expression_count: int
    summary: str | None = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


# ── Scene Generation ──────────────────────────────────────────

class SceneGenerateResponse(SQLModel):
    scene_card_id: uuid.UUID
    scene: "SceneCardRead"
