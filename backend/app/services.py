"""CRUD services for major models.

Each service receives a SQLModel Session and provides:
- get(id)        → single instance or None
- get_all(skip, limit) → (items, total) for paginated listing
- create(payload) → new instance
- update(id, payload) → updated instance or None
- delete(id)      → True if deleted, False if not found
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select, func

from . import models as m


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════

def get_profile(*, session: Session, profile_id: uuid.UUID) -> m.Profile | None:
    return session.get(m.Profile, profile_id)


def get_all_profiles(*, session: Session, skip: int = 0, limit: int = 50) -> tuple[list[m.Profile], int]:
    total = session.exec(select(func.count()).select_from(m.Profile)).one()  # type: ignore[arg-type]
    items = session.exec(select(m.Profile).offset(skip).limit(limit)).all()
    return list(items), total


def create_profile(*, session: Session, data: Any) -> m.Profile:
    profile = m.Profile(**data.model_dump())
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def update_profile(*, session: Session, profile_id: uuid.UUID, data: Any) -> m.Profile | None:
    profile = session.get(m.Profile, profile_id)
    if not profile:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, val)
    profile.updated_at = _utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def delete_profile(*, session: Session, profile_id: uuid.UUID) -> bool:
    profile = session.get(m.Profile, profile_id)
    if not profile:
        return False
    session.delete(profile)
    session.commit()
    return True


# ═══════════════════════════════════════════════════════════════
# Material
# ═══════════════════════════════════════════════════════════════

def get_material(*, session: Session, material_id: uuid.UUID) -> m.Material | None:
    return session.get(m.Material, material_id)


def get_all_materials(*, session: Session, skip: int = 0, limit: int = 50) -> tuple[list[m.Material], int]:
    total = session.exec(select(func.count()).select_from(m.Material)).one()  # type: ignore[arg-type]
    items = session.exec(select(m.Material).offset(skip).limit(limit)).all()
    return list(items), total


def create_material(*, session: Session, data: Any) -> m.Material:
    material = m.Material(**data.model_dump())
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def update_material(*, session: Session, material_id: uuid.UUID, data: Any) -> m.Material | None:
    material = session.get(m.Material, material_id)
    if not material:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(material, key, val)
    material.updated_at = _utcnow()
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def delete_material(*, session: Session, material_id: uuid.UUID) -> bool:
    material = session.get(m.Material, material_id)
    if not material:
        return False
    session.delete(material)
    session.commit()
    return True


# ═══════════════════════════════════════════════════════════════
# SceneCard
# ═══════════════════════════════════════════════════════════════

def get_scene_card(*, session: Session, scene_id: uuid.UUID) -> m.SceneCard | None:
    return session.get(m.SceneCard, scene_id)


def get_all_scene_cards(*, session: Session, skip: int = 0, limit: int = 50) -> tuple[list[m.SceneCard], int]:
    total = session.exec(select(func.count()).select_from(m.SceneCard)).one()  # type: ignore[arg-type]
    items = session.exec(select(m.SceneCard).offset(skip).limit(limit)).all()
    return list(items), total


def create_scene_card(*, session: Session, data: Any) -> m.SceneCard:
    card = m.SceneCard(**data.model_dump())
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def update_scene_card(*, session: Session, scene_id: uuid.UUID, data: Any) -> m.SceneCard | None:
    card = session.get(m.SceneCard, scene_id)
    if not card:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(card, key, val)
    card.updated_at = _utcnow()
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def delete_scene_card(*, session: Session, scene_id: uuid.UUID) -> bool:
    card = session.get(m.SceneCard, scene_id)
    if not card:
        return False
    session.delete(card)
    session.commit()
    return True


# ═══════════════════════════════════════════════════════════════
# PracticeSession
# ═══════════════════════════════════════════════════════════════

def get_session(*, session: Session, session_id: uuid.UUID) -> m.PracticeSession | None:
    return session.get(m.PracticeSession, session_id)


def get_all_sessions(*, session: Session, skip: int = 0, limit: int = 50) -> tuple[list[m.PracticeSession], int]:
    total = session.exec(select(func.count()).select_from(m.PracticeSession)).one()  # type: ignore[arg-type]
    items = session.exec(select(m.PracticeSession).offset(skip).limit(limit)).all()
    return list(items), total


def create_session(*, session: Session, data: Any) -> m.PracticeSession:
    ps = m.PracticeSession(**data.model_dump())
    session.add(ps)
    session.commit()
    session.refresh(ps)
    return ps


def update_session(*, session: Session, session_id: uuid.UUID, data: Any) -> m.PracticeSession | None:
    ps = session.get(m.PracticeSession, session_id)
    if not ps:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(ps, key, val)
    ps.updated_at = _utcnow()
    session.add(ps)
    session.commit()
    session.refresh(ps)
    return ps


def delete_session(*, session: Session, session_id: uuid.UUID) -> bool:
    ps = session.get(m.PracticeSession, session_id)
    if not ps:
        return False
    session.delete(ps)
    session.commit()
    return True


# ═══════════════════════════════════════════════════════════════
# PersonalExpressionReport
# ═══════════════════════════════════════════════════════════════

def get_report(*, session: Session, report_id: uuid.UUID) -> m.PersonalExpressionReport | None:
    return session.get(m.PersonalExpressionReport, report_id)


def get_all_reports(*, session: Session, skip: int = 0, limit: int = 50) -> tuple[list[m.PersonalExpressionReport], int]:
    total = session.exec(select(func.count()).select_from(m.PersonalExpressionReport)).one()  # type: ignore[arg-type]
    items = session.exec(select(m.PersonalExpressionReport).offset(skip).limit(limit)).all()
    return list(items), total


def create_report(*, session: Session, data: Any) -> m.PersonalExpressionReport:
    report = m.PersonalExpressionReport(**data.model_dump())
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def delete_report(*, session: Session, report_id: uuid.UUID) -> bool:
    report = session.get(m.PersonalExpressionReport, report_id)
    if not report:
        return False
    session.delete(report)
    session.commit()


# ── Shared helpers ────────────────────────────────────────────

def scene_to_dict(scene: m.SceneCard) -> dict:
    """Convert a SceneCard ORM object to the dict shape consumed by ConversationAgent.

    Used by both text-turn (sessions.py) and voice-turn (voice.py) routes.
    """
    return {
        "title": scene.title,
        "scene_type": scene.scene_type,
        "style": scene.style,
        "difficulty": scene.difficulty,
        "ai_role": scene.ai_role,
        "user_role": scene.user_role,
        "task_goal": scene.task_goal,
        "opening_question": scene.opening_question,
        "follow_up_strategy": scene.follow_up_strategy,
        "must_cover_points": scene.must_cover_points,
    }
    return True
