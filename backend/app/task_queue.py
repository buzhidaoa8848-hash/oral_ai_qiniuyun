"""Optional background task queue via Redis/RQ.

If Redis is not available, tasks run inline synchronously — no configuration needed.

Redis setup (optional):
    REDIS_URL=redis://localhost:6379/0
    pip install rq

Tasks:
    evaluate_turn(session_id, user_turn_id, eval_context_dict)
    generate_report(session_id)
    process_material(material_id, scene_config_dict)

Usage:
    from .task_queue import enqueue
    enqueue("evaluate_turn", session_id=..., user_turn_id=..., ...)
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger("scenetalk.task_queue")

# ── Detect Redis/RQ ───────────────────────────────────────────
_RQ_AVAILABLE = False
try:
    from redis import Redis as _Redis
    from rq import Queue as _Queue

    _r = _Redis.from_url("redis://localhost:6379/0", socket_connect_timeout=1)
    _r.ping()
    _queue = _Queue(connection=_r)
    _RQ_AVAILABLE = True
    logger.info("Task queue: Redis/RQ available — background jobs enabled")
except Exception:
    logger.info("Task queue: Redis/RQ not available — tasks will run inline")


# ── Task implementations ──────────────────────────────────────

def _task_evaluate_turn(session_id: str, user_turn_id: str, eval_context_dict: dict) -> None:
    """Background: run the evaluation pipeline for a turn."""
    import uuid
    from sqlmodel import Session
    from .database import engine
    from .agents.pipeline import EvaluationPipeline
    from .agents.schemas import EvalContext

    logger.info(f"Task: evaluate_turn session={session_id} turn={user_turn_id}")
    ctx = EvalContext(**eval_context_dict)
    with Session(engine) as db:
        pipeline = EvaluationPipeline()
        pipeline.run(db=db, user_turn_id=uuid.UUID(user_turn_id), ctx=ctx)
    logger.info(f"Task: evaluate_turn done session={session_id}")


def _task_generate_report(session_id: str) -> dict[str, Any]:
    """Background: generate a session report."""
    import uuid
    from sqlmodel import Session
    from .database import engine
    from .agents.report_agent import ReportAgent

    logger.info(f"Task: generate_report session={session_id}")
    with Session(engine) as db:
        agent = ReportAgent()
        report = agent.generate(db=db, session_id=uuid.UUID(session_id))
    logger.info(f"Task: generate_report done session={session_id}")
    return report


def _task_process_material(material_id: str, scene_config: dict) -> str:
    """Background: run SceneBuilderAgent on a material."""
    import uuid
    from sqlmodel import Session
    from .database import engine
    from . import models as m
    from .scene_builder import build_and_save_scene

    logger.info(f"Task: process_material material={material_id}")
    with Session(engine) as db:
        material = db.get(m.Material, uuid.UUID(material_id))
        if not material:
            raise ValueError(f"Material {material_id} not found")
        card, _ = build_and_save_scene(
            session=db,
            material=material,
            scene_type=scene_config.get("scene_type", "conversation"),
            style=scene_config.get("style", "casual"),
            user_level=scene_config.get("user_level", "B1"),
            target_goal=scene_config.get("target_goal", ""),
        )
    logger.info(f"Task: process_material done → scene={card.id}")
    return str(card.id)


_TASK_MAP: dict[str, Callable[..., Any]] = {
    "evaluate_turn": _task_evaluate_turn,
    "generate_report": _task_generate_report,
    "process_material": _task_process_material,
}


# ── Public API ────────────────────────────────────────────────

def enqueue(task_name: str, **kwargs: Any) -> Any:
    """Enqueue a background task, or run it inline if Redis is unavailable."""
    if task_name not in _TASK_MAP:
        raise ValueError(f"Unknown task: {task_name}. Available: {list(_TASK_MAP)}")

    if _RQ_AVAILABLE:
        logger.info(f"Enqueuing task: {task_name} (Redis/RQ)")
        return _queue.enqueue(_TASK_MAP[task_name], **kwargs)
    else:
        logger.info(f"Running task inline: {task_name}")
        return _TASK_MAP[task_name](**kwargs)
