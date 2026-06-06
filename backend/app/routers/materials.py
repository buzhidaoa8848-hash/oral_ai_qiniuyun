"""Material CRUD + paste text + file upload + scene generation."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlmodel import Session

from ..database import get_session
from .. import models as m, schemas, services
from ..scene_builder import build_and_save_scene

router = APIRouter(prefix="/api/materials", tags=["materials"])

# ── Allowed upload extensions ──────────────────────────────────
_ALLOWED_EXTENSIONS = {".txt", ".md", ".srt", ".vtt"}


# ── CRUD ───────────────────────────────────────────────────────

@router.get("", response_model=list[schemas.MaterialRead])
def list_materials(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    items, _ = services.get_all_materials(session=session, skip=skip, limit=limit)
    return items


@router.get("/{material_id}", response_model=schemas.MaterialRead)
def get_material(material_id: uuid.UUID, session: Session = Depends(get_session)):
    material = services.get_material(session=session, material_id=material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.delete("/{material_id}", status_code=204)
def delete_material(material_id: uuid.UUID, session: Session = Depends(get_session)):
    ok = services.delete_material(session=session, material_id=material_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Material not found")


# ── Paste text ─────────────────────────────────────────────────

@router.post("", response_model=schemas.MaterialRead, status_code=201)
def create_material_from_paste(
    data: schemas.MaterialPasteIn,
    session: Session = Depends(get_session),
):
    """Accept pasted text and store it as a Material."""
    mat = m.Material(
        title=data.title,
        content=data.raw_text[:500],  # short preview
        material_type="text",
        language=data.language,
        raw_text=data.raw_text,
        source_type="paste",
        metadata_json=data.metadata_json,
    )
    session.add(mat)
    session.commit()
    session.refresh(mat)
    return mat


# ── File upload ────────────────────────────────────────────────

@router.post("/upload", response_model=schemas.MaterialRead, status_code=201)
async def upload_material(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Upload a .txt / .md / .srt / .vtt file as a Material."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}",
        )

    raw = (await file.read()).decode("utf-8", errors="replace")
    title = Path(file.filename).stem

    mat = m.Material(
        title=title,
        content=raw[:500],
        material_type="text",
        language="en",
        raw_text=raw,
        source_type=ext.lstrip("."),
    )
    session.add(mat)
    session.commit()
    session.refresh(mat)
    return mat


# ── Scene generation ───────────────────────────────────────────

@router.post("/{material_id}/generate-scene", response_model=schemas.SceneGenerateResponse)
def generate_scene_from_material(
    material_id: uuid.UUID,
    req: schemas.SceneGenerateRequest,
    session: Session = Depends(get_session),
):
    """Run the Scene Builder Agent on a Material to produce a SceneCard."""
    material = services.get_material(session=session, material_id=material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    card, _scene_data = build_and_save_scene(
        session=session,
        material=material,
        scene_type=req.scene_type,
        style=req.style,
        user_level=req.user_level,
        target_goal=req.target_goal,
    )

    # Build read response
    scene_read = schemas.SceneCardRead(
        id=card.id,
        title=card.title,
        difficulty=card.difficulty,
        topic=card.topic,
        scene_type=card.scene_type,
        style=card.style,
        ai_role=card.ai_role,
        user_role=card.user_role,
        task_goal=card.task_goal,
        key_expressions=card.key_expressions,
        must_cover_points=card.must_cover_points,
        follow_up_strategy=card.follow_up_strategy,
        evaluation_rubric=card.evaluation_rubric,
        opening_question=card.opening_question,
        prompt=card.prompt,
        character_role=card.character_role,
        model_answer=card.model_answer,
        hints=card.hints,
        target_language=card.target_language,
        source_language=card.source_language,
        tags=card.tags,
        material_id=card.material_id,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )
    return schemas.SceneGenerateResponse(scene_card_id=card.id, scene=scene_read)
