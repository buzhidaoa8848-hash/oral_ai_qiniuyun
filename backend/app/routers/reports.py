"""Report routes — session reports + CRUD for legacy reports."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..database import get_session as get_db_dep
from .. import schemas, services
from ..agents.report_agent import ReportAgent

router = APIRouter(prefix="/api/reports", tags=["reports"])

# ── Legacy CRUD ───────────────────────────────────────────────

@router.get("", response_model=list[schemas.ReportRead])
def list_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_dep),
):
    items, _ = services.get_all_reports(session=db, skip=skip, limit=limit)
    return items


@router.get("/{report_id}", response_model=schemas.ReportRead)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    report = services.get_report(session=db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("", response_model=schemas.ReportRead, status_code=201)
def create_report(data: schemas.ReportCreate, db: Session = Depends(get_db_dep)):
    return services.create_report(session=db, data=data)


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    ok = services.delete_report(session=db, report_id=report_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")


# ── Session report ────────────────────────────────────────────

@router.get("/session/{session_id}")
def get_session_report(session_id: uuid.UUID, db: Session = Depends(get_db_dep)):
    """Generate a full session report."""
    try:
        agent = ReportAgent()
        report = agent.generate(db=db, session_id=session_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
