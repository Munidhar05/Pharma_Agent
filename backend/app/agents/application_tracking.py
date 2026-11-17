import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.application import ApplicationRecord, ApplicationEvent
from backend.app.models.job import DiscoveredJob
from backend.app.models.company import Company
from backend.app.models.audit import Notification
from backend.app.schemas.application import ApplicationStatsResponse

logger = logging.getLogger(__name__)


class ApplicationTrackingAgent:
    """
    Agent 10: Application Tracking Agent.
    Monitors application lifecycle states, prevents duplicate submissions,
    and logs comprehensive audit events across all stages.
    """

    ALLOWED_STATUSES = [
        "Discovered",
        "Matched",
        "Shortlisted",
        "Resume generated",
        "Awaiting approval",
        "Submitted",
        "Application confirmed",
        "Assessment pending",
        "Interview scheduled",
        "Offer received",
        "Rejected",
        "Withdrawn",
        "Closed"
    ]

    def __init__(self, db: Session):
        self.db = db

    def check_duplicate_application(
        self, candidate_id: int, job_id: int
    ) -> Tuple[bool, Optional[ApplicationRecord], Optional[str]]:
        """
        Checks whether the candidate has already applied to this specific job
        or recently applied to the same company for a similar role.
        Returns: (is_duplicate: bool, existing_record, reason: Optional[str])
        """
        # Exact job duplicate check
        existing = (
            self.db.query(ApplicationRecord)
            .filter(
                ApplicationRecord.candidate_id == candidate_id,
                ApplicationRecord.job_id == job_id
            )
            .first()
        )
        if existing:
            return True, existing, f"Candidate already has an application record (status: {existing.status}) for this job."

        # Company-level recent application check (prevent spamming same company within 14 days)
        target_job = self.db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
        if target_job:
            fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
            recent_company_app = (
                self.db.query(ApplicationRecord)
                .join(DiscoveredJob, ApplicationRecord.job_id == DiscoveredJob.id)
                .filter(
                    ApplicationRecord.candidate_id == candidate_id,
                    DiscoveredJob.company_id == target_job.company_id,
                    ApplicationRecord.created_at >= fourteen_days_ago,
                    ApplicationRecord.status.in_(["Submitted", "Application confirmed", "Awaiting approval"])
                )
                .first()
            )
            if recent_company_app:
                # Return warning info but don't strictly block unless same requisition
                logger.info(
                    f"Candidate has a recent application to company {target_job.company_id} within 14 days."
                )

        return False, None, None

    def record_event(
        self,
        application_id: int,
        previous_status: Optional[str],
        new_status: str,
        event_source: str = "Agent",
        notes: Optional[str] = None
    ) -> ApplicationEvent:
        """
        Logs an immutable audit event for application state changes.
        """
        event = ApplicationEvent(
            application_id=application_id,
            previous_status=previous_status,
            new_status=new_status,
            event_source=event_source,
            notes=notes,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def transition_status(
        self,
        application_id: int,
        new_status: str,
        event_source: str = "Agent",
        notes: Optional[str] = None,
        submission_ref_id: Optional[str] = None
    ) -> ApplicationRecord:
        """
        Transitions an application record to a new status and logs the audit event.
        """
        app_record = (
            self.db.query(ApplicationRecord)
            .filter(ApplicationRecord.id == application_id)
            .first()
        )
        if not app_record:
            raise ValueError(f"Application record with ID {application_id} not found.")

        old_status = app_record.status
        app_record.status = new_status
        app_record.updated_at = datetime.utcnow()
        app_record.last_checked_at = datetime.utcnow()

        if submission_ref_id:
            app_record.submission_ref_id = submission_ref_id

        if new_status in ["Submitted", "Application confirmed"] and not app_record.applied_at:
            app_record.applied_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(app_record)

        # Record audit event
        self.record_event(
            application_id=app_record.id,
            previous_status=old_status,
            new_status=new_status,
            event_source=event_source,
            notes=notes or f"Application status updated from '{old_status}' to '{new_status}'."
        )

        # Trigger in-app notification if status is an important milestone
        self._notify_milestone(app_record, old_status, new_status)

        return app_record

    def _notify_milestone(self, app_record: ApplicationRecord, old_status: str, new_status: str):
        """Dispatches an in-app notification for significant status milestones."""
        try:
            user_id = app_record.candidate_profile.user_id if app_record.candidate_profile else None
            if not user_id:
                return

            job_title = app_record.job.title if app_record.job else "Position"
            company_name = app_record.job.company.name if (app_record.job and app_record.job.company) else "Pharma Company"

            if new_status == "Interview scheduled":
                notif = Notification(
                    user_id=user_id,
                    title=f"🎉 Interview Scheduled: {company_name}",
                    message=f"Congratulations! An interview has been scheduled for {job_title} at {company_name}.",
                    notification_type="interview",
                    is_read=False
                )
                self.db.add(notif)
                self.db.commit()

            elif new_status == "Assessment pending":
                notif = Notification(
                    user_id=user_id,
                    title=f"📝 Assessment Received: {company_name}",
                    message=f"An assessment test or coding challenge is pending for {job_title} at {company_name}.",
                    notification_type="assessment",
                    is_read=False
                )
                self.db.add(notif)
                self.db.commit()

            elif new_status == "Application confirmed":
                notif = Notification(
                    user_id=user_id,
                    title=f"✅ Application Confirmed: {company_name}",
                    message=f"Your application for {job_title} at {company_name} was successfully submitted and confirmed (Ref: {app_record.submission_ref_id or 'N/A'}).",
                    notification_type="application_confirmed",
                    is_read=False
                )
                self.db.add(notif)
                self.db.commit()

        except Exception as e:
            logger.warning(f"Failed to create milestone notification: {e}")

    def get_application_stats(self, candidate_id: int) -> ApplicationStatsResponse:
        """
        Calculates application count statistics grouped by lifecycle stages.
        """
        records = (
            self.db.query(ApplicationRecord)
            .filter(ApplicationRecord.candidate_id == candidate_id)
            .all()
        )

        total = len(records)
        awaiting_approval = sum(1 for r in records if r.status == "Awaiting approval")
        submitted = sum(1 for r in records if r.status == "Submitted")
        confirmed = sum(1 for r in records if r.status == "Application confirmed")
        interviews = sum(1 for r in records if r.status == "Interview scheduled")
        assessments = sum(1 for r in records if r.status == "Assessment pending")
        offers = sum(1 for r in records if r.status == "Offer received")
        rejections = sum(1 for r in records if r.status == "Rejected")

        return ApplicationStatsResponse(
            total_applications=total,
            awaiting_approval=awaiting_approval,
            submitted=submitted,
            confirmed=confirmed,
            interviews=interviews,
            assessments=assessments,
            offers=offers,
            rejections=rejections
        )
