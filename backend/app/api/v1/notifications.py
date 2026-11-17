from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.audit import Notification
from backend.app.schemas.notification import (
    NotificationResponse,
    NotificationCreate,
    NotificationBatchReadRequest
)
from backend.app.services.scheduler import autonomous_scheduler

router = APIRouter(tags=["Notifications & Scheduler"])


def _unwrap_val(val, default):
    """Safely extracts value if called directly in tests where FastAPI Query object is passed."""
    if hasattr(val, "default"):
        return val.default
    return val if val is not None else default


@router.get("/notifications", response_model=List[NotificationResponse])
def list_notifications(
    user_id: Optional[int] = Query(None, description="User ID"),
    is_read: Optional[bool] = Query(None, description="Filter read status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List user notifications with optional unread filter.
    """
    u_id = _unwrap_val(user_id, None)
    read_filter = _unwrap_val(is_read, None)
    sk = _unwrap_val(skip, 0)
    lm = _unwrap_val(limit, 50)

    query = db.query(Notification)
    if u_id:
        query = query.filter(Notification.user_id == u_id)
    if read_filter is not None:
        query = query.filter(Notification.is_read == read_filter)

    records = query.order_by(Notification.sent_at.desc()).offset(sk).limit(lm).all()
    return records


@router.get("/notifications/unread-count")
def get_unread_count(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Returns unread notification badge count for the user.
    """
    u_id = _unwrap_val(user_id, 1)
    count = (
        db.query(Notification)
        .filter(Notification.user_id == u_id, Notification.is_read == False)
        .count()
    )
    return {"user_id": u_id, "unread_count": count}


@router.patch("/notifications/{id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Marks a specific notification as read.
    """
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(status_code=404, detail=f"Notification {id} not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    request: NotificationBatchReadRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Marks all (or a batch of) notifications as read.
    """
    u_id = _unwrap_val(user_id, 1)
    query = db.query(Notification).filter(Notification.user_id == u_id)
    if request.notification_ids:
        query = query.filter(Notification.id.in_(request.notification_ids))

    updated_count = query.update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"message": f"{updated_count} notifications marked as read."}


@router.get("/scheduler/status")
def get_scheduler_status():
    """
    Returns the execution status and schedule intervals of all autonomous background tasks.
    """
    return autonomous_scheduler.get_status()


@router.post("/scheduler/trigger/{task_name}")
def trigger_scheduled_task(task_name: str):
    """
    Immediately runs an autonomous agent cycle (job_discovery, job_verification, candidate_matching, company_discovery).
    """
    try:
        result = autonomous_scheduler.run_task_now(task_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
