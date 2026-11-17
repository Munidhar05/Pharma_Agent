from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.application import ApplicationRecord, ApplicationEvent
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import DiscoveredJob
from backend.app.schemas.application import (
    ApplicationRecordCreate,
    ApplicationApprovalRequest,
    ApplicationStatusUpdateRequest,
    ApplicationPreviewResponse,
    ApplicationSubmissionResult,
    ApplicationRecordResponse,
    ApplicationEventResponse,
    ApplicationStatsResponse,
)
from backend.app.agents.application_automation import ApplicationAutomationAgent
from backend.app.agents.application_tracking import ApplicationTrackingAgent

router = APIRouter(prefix="/applications", tags=["Application Automation & Tracking"])


def _unwrap_val(val, default):
    """Safely extracts value if called directly in tests where FastAPI Query object is passed."""
    if hasattr(val, "default"):
        return val.default
    return val if val is not None else default


@router.get("", response_model=List[ApplicationRecordResponse])
def list_applications(
    candidate_id: Optional[int] = Query(None, description="Filter by candidate ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List applications with optional candidate or status filtering.
    """
    c_id = _unwrap_val(candidate_id, None)
    s_filter = _unwrap_val(status, None)
    sk = _unwrap_val(skip, 0)
    lm = _unwrap_val(limit, 50)

    query = db.query(ApplicationRecord)

    if c_id:
        query = query.filter(ApplicationRecord.candidate_id == c_id)
    if s_filter:
        query = query.filter(ApplicationRecord.status == s_filter)

    records = query.order_by(ApplicationRecord.updated_at.desc()).offset(sk).limit(lm).all()

    response_list = []
    for r in records:
        resp = ApplicationRecordResponse.model_validate(r)
        if r.job:
            resp.job_title = r.job.title
            resp.location = r.job.location
            if r.job.company:
                resp.company_name = r.job.company.name
        response_list.append(resp)

    return response_list


@router.get("/stats", response_model=ApplicationStatsResponse)
def get_application_statistics(
    candidate_id: int = Query(..., description="Candidate profile ID"),
    db: Session = Depends(get_db)
):
    """
    Returns application count metrics grouped by lifecycle states for the candidate dashboard.
    """
    c_id = _unwrap_val(candidate_id, 1)
    tracking_agent = ApplicationTrackingAgent(db)
    return tracking_agent.get_application_stats(c_id)


@router.post("/prepare", response_model=ApplicationPreviewResponse)
def prepare_application(
    request: ApplicationRecordCreate,
    db: Session = Depends(get_db)
):
    """
    Prepares a job application:
    - Verifies active status
    - Prepares ATS tailored resume
    - Maps profile to form fields
    - Solves screening questions truthfully
    - Halts at approval gate
    """
    automation_agent = ApplicationAutomationAgent(db)
    try:
        preview = automation_agent.prepare_application(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            resume_id=request.resume_id,
            mode=request.mode or "Assisted application with approval"
        )
        return preview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}/preview", response_model=ApplicationPreviewResponse)
def get_application_preview(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Fetches the mapped form preview and readiness snapshot for an application.
    """
    automation_agent = ApplicationAutomationAgent(db)
    try:
        return automation_agent.get_application_preview(id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{id}/approve", response_model=ApplicationRecordResponse)
def approve_application(
    id: int,
    approval: ApplicationApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Candidate provides explicit approval to submit the application.
    May supply custom or verified screening question overrides.
    """
    automation_agent = ApplicationAutomationAgent(db)
    try:
        record = automation_agent.approve_application(
            application_id=id,
            notes=approval.notes,
            custom_screening_answers=approval.custom_screening_answers
        )
        resp = ApplicationRecordResponse.model_validate(record)
        if record.job:
            resp.job_title = record.job.title
            resp.location = record.job.location
            if record.job.company:
                resp.company_name = record.job.company.name
        return resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/submit", response_model=ApplicationSubmissionResult)
def submit_application(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Submits an application in assisted mode.
    Strictly blocked if candidate explicit approval has not been given.
    """
    automation_agent = ApplicationAutomationAgent(db)
    try:
        return automation_agent.submit_application(id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{id}/status", response_model=ApplicationRecordResponse)
def update_application_status(
    id: int,
    update_req: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates the lifecycle status of an application (e.g., Interview scheduled, Assessment received).
    """
    tracking_agent = ApplicationTrackingAgent(db)
    try:
        record = tracking_agent.transition_status(
            application_id=id,
            new_status=update_req.new_status,
            event_source=update_req.event_source or "Candidate",
            notes=update_req.notes,
            submission_ref_id=update_req.submission_ref_id
        )
        resp = ApplicationRecordResponse.model_validate(record)
        if record.job:
            resp.job_title = record.job.title
            resp.location = record.job.location
            if record.job.company:
                resp.company_name = record.job.company.name
        return resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}/events", response_model=List[ApplicationEventResponse])
def get_application_events(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Returns the immutable audit event log for an application.
    """
    app_record = db.query(ApplicationRecord).filter(ApplicationRecord.id == id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail=f"Application record with ID {id} not found.")

    events = (
        db.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == id)
        .order_by(ApplicationEvent.created_at.asc())
        .all()
    )
    return [ApplicationEventResponse.model_validate(e) for e in events]

