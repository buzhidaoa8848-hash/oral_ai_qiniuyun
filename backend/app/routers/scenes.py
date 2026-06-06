"""SceneCard CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..database import get_session
from .. import schemas, services

router = APIRouter(prefix="/api/scenes", tags=["scenes"])


@router.get("", response_model=list[schemas.SceneCardRead])
def list_scene_cards(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    items, _ = services.get_all_scene_cards(session=session, skip=skip, limit=limit)
    return items


@router.get("/{scene_id}", response_model=schemas.SceneCardRead)
def get_scene_card(scene_id: uuid.UUID, session: Session = Depends(get_session)):
    card = services.get_scene_card(session=session, scene_id=scene_id)
    if not card:
        raise HTTPException(status_code=404, detail="SceneCard not found")
    return card


@router.post("", response_model=schemas.SceneCardRead, status_code=201)
def create_scene_card(data: schemas.SceneCardCreate, session: Session = Depends(get_session)):
    return services.create_scene_card(session=session, data=data)


@router.put("/{scene_id}", response_model=schemas.SceneCardRead)
def update_scene_card(scene_id: uuid.UUID, data: schemas.SceneCardUpdate, session: Session = Depends(get_session)):
    card = services.update_scene_card(session=session, scene_id=scene_id, data=data)
    if not card:
        raise HTTPException(status_code=404, detail="SceneCard not found")
    return card


@router.delete("/{scene_id}", status_code=204)
def delete_scene_card(scene_id: uuid.UUID, session: Session = Depends(get_session)):
    ok = services.delete_scene_card(session=session, scene_id=scene_id)
    if not ok:
        raise HTTPException(status_code=404, detail="SceneCard not found")
