"""Profile CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..database import get_session
from .. import schemas, services

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("", response_model=list[schemas.ProfileRead])
def list_profiles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    items, _ = services.get_all_profiles(session=session, skip=skip, limit=limit)
    return items


@router.get("/{profile_id}", response_model=schemas.ProfileRead)
def get_profile(profile_id: uuid.UUID, session: Session = Depends(get_session)):
    profile = services.get_profile(session=session, profile_id=profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("", response_model=schemas.ProfileRead, status_code=201)
def create_profile(data: schemas.ProfileCreate, session: Session = Depends(get_session)):
    return services.create_profile(session=session, data=data)


@router.put("/{profile_id}", response_model=schemas.ProfileRead)
def update_profile(profile_id: uuid.UUID, data: schemas.ProfileUpdate, session: Session = Depends(get_session)):
    profile = services.update_profile(session=session, profile_id=profile_id, data=data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: uuid.UUID, session: Session = Depends(get_session)):
    ok = services.delete_profile(session=session, profile_id=profile_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Profile not found")
