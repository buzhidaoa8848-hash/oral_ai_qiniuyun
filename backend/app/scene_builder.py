"""SceneBuilderAgent — turns a Material into a structured SceneCard via LLM.

Flow:
  material_text + scene_type + style + user_level + target_goal
    → LLM (or mock) → Pydantic validation → SceneCardCreate JSON
    → fallback if anything fails
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session

from . import models as m
from . import schemas
from .providers import get_provider
from .schemas import SceneCardCreate

# ── Prompt template ────────────────────────────────────────────

_SCENE_GEN_PROMPT = """You are a language-learning content designer. Given a source text, create a SceneCard for speaking practice.

## Source Text (transcript / dialogue / article)
{source_text}

## Requirements
- Scene type: {scene_type}
- Style: {style}
- User proficiency level: {user_level}
- Target goal: {target_goal}

## Output a JSON object with these keys:
- title (string, max 256 chars)
- difficulty (one of: A1, A2, B1, B2, C1, C2 — pick based on user_level)
- topic (string)
- scene_type (same as input)
- style (same as input)
- ai_role (string — who the AI plays in the dialogue)
- user_role (string — who the user plays)
- task_goal (string — what the user must accomplish)
- key_expressions (array of 3-5 useful phrases from the source or relevant to the scene)
- must_cover_points (array of 3-4 bullet points the user must address)
- follow_up_strategy (string — how the AI should push back or probe)
- evaluation_rubric (string — scoring criteria with percentages)
- opening_question (string — the first line the AI says to start the conversation)
- prompt (short scene description)
- character_role (short label for the user's role)
- model_answer (empty string)
- tags (array of 2-4 topic tags)

Return ONLY the JSON object, no explanations."""

# ── Fallback template ──────────────────────────────────────────

_FALLBACK_SCENE: dict[str, Any] = {
    "title": "Practice Conversation",
    "difficulty": "B1",
    "topic": "General",
    "scene_type": "conversation",
    "style": "casual",
    "ai_role": "Practice Partner",
    "user_role": "Learner",
    "task_goal": "Have a natural conversation based on the provided material.",
    "key_expressions": [
        "Could you repeat that?",
        "I think that…",
        "What do you mean by…?",
    ],
    "must_cover_points": [
        "Greet and start the conversation",
        "Discuss the main topic from the material",
        "Ask at least one follow-up question",
    ],
    "follow_up_strategy": "Ask open-ended questions to keep the conversation flowing.",
    "evaluation_rubric": "Fluency (30%) · Accuracy (25%) · Relevance (25%) · Interaction (20%)",
    "opening_question": "Hi! Let's practice. I read something interesting — can we talk about it?",
    "prompt": "Practice a conversation based on the provided material.",
    "character_role": "Learner",
    "model_answer": "",
    "hints": ["use the material as inspiration", "be natural"],
    "tags": ["practice", "conversation"],
    "target_language": "en",
    "source_language": "en",
}


# ── Agent ──────────────────────────────────────────────────────

class SceneBuilderAgent:
    """Orchestrates scene generation: provider → validate → fallback."""

    def generate(
        self,
        *,
        material_text: str,
        scene_type: str,
        style: str,
        user_level: str,
        target_goal: str,
    ) -> SceneCardCreate:
        """Generate a validated SceneCardCreate from the given inputs.

        Returns a deterministic fallback if the LLM fails.
        """
        prompt = _SCENE_GEN_PROMPT.format(
            source_text=material_text[:3000],  # truncate for token limits
            scene_type=scene_type,
            style=style,
            user_level=user_level,
            target_goal=target_goal or "Practice speaking naturally",
        )

        provider = get_provider()
        try:
            raw = provider.generate_json(prompt, {})  # schema ignored by mock
            validated = self._validate(raw, scene_type, style)
            if validated:
                return validated
        except Exception as exc:
            # Log the error in production; for now, fall back silently
            pass

        return self._fallback(scene_type, style)

    def _validate(
        self, raw: dict[str, Any], scene_type: str, style: str
    ) -> SceneCardCreate | None:
        """Pydantic-validate raw dict → SceneCardCreate. Returns None on failure."""
        try:
            # Ensure required fields from the request are set
            raw.setdefault("scene_type", scene_type)
            raw.setdefault("style", style)
            raw.setdefault("difficulty", "B1")
            raw.setdefault("topic", "General")
            raw.setdefault("model_answer", "")
            raw.setdefault("prompt", "")
            raw.setdefault("character_role", raw.get("user_role", "Learner"))
            raw.setdefault("task_goal", "")
            raw.setdefault("follow_up_strategy", "")
            raw.setdefault("evaluation_rubric", "")
            raw.setdefault("opening_question", "")
            raw.setdefault("tags", [])
            raw.setdefault("key_expressions", [])
            raw.setdefault("must_cover_points", [])
            raw.setdefault("hints", None)
            raw.setdefault("material_id", None)
            return SceneCardCreate(**raw)
        except Exception:
            return None

    def _fallback(self, scene_type: str, style: str) -> SceneCardCreate:
        """Deterministic fallback SceneCard — always succeeds."""
        data = dict(_FALLBACK_SCENE)
        data["scene_type"] = scene_type
        data["style"] = style
        return SceneCardCreate(**data)


# ── Service-level helper ───────────────────────────────────────

def build_and_save_scene(
    *,
    session: Session,
    material: m.Material,
    scene_type: str,
    style: str,
    user_level: str,
    target_goal: str,
) -> tuple[m.SceneCard, SceneCardCreate]:
    """Full pipeline: generate → validate → persist → return."""
    agent = SceneBuilderAgent()
    scene_data = agent.generate(
        material_text=material.raw_text or material.content,
        scene_type=scene_type,
        style=style,
        user_level=user_level,
        target_goal=target_goal,
    )

    payload = scene_data.model_dump()
    payload["material_id"] = material.id
    card = m.SceneCard(**payload)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card, scene_data
