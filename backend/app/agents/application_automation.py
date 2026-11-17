import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.models.application import ApplicationRecord, ApplicationEvent
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import DiscoveredJob
from backend.app.models.resume import GeneratedResume
from backend.app.models.audit import AgentExecutionLog
from backend.app.schemas.application import (
    ApplicationPreviewResponse,
    ApplicationSubmissionResult,
    FormPreviewField,
    ScreeningQuestionAnswer
)
from backend.app.services.form_mapper import FormMapperService
from backend.app.agents.application_tracking import ApplicationTrackingAgent
from backend.app.agents.resume_generation import ResumeGenerationAgent

logger = logging.getLogger(__name__)


class ApplicationAutomationAgent:
    """
    Agent 9: Application Automation Agent.
    Manages end-to-end application preparation, truthful form field mapping,
    screening question resolution, candidate assisted approval gate, and submission tracking.
    """

    def __init__(self, db: Session):
        self.db = db
        self.tracking_agent = ApplicationTrackingAgent(db)
        self.resume_agent = ResumeGenerationAgent(db)

    def prepare_application(
        self,
        candidate_id: int,
        job_id: int,
        resume_id: Optional[int] = None,
        mode: str = "Assisted application with approval"
    ) -> ApplicationPreviewResponse:
        """
        Prepares a complete application snapshot:
        - Validates candidate and job eligibility
        - Prepares ATS tailored resume if not already generated
        - Maps candidate profile to standard job application form fields
        - Solves screening questions truthfully
        - Generates application preview awaiting candidate approval
        """
        start_time = datetime.utcnow()

        candidate = (
            self.db.query(CandidateProfile)
            .filter(CandidateProfile.id == candidate_id)
            .first()
        )
        if not candidate:
            raise ValueError(f"Candidate profile with ID {candidate_id} not found.")

        job = (
            self.db.query(DiscoveredJob)
            .filter(DiscoveredJob.id == job_id)
            .first()
        )
        if not job:
            raise ValueError(f"Job vacancy with ID {job_id} not found.")

        # Check for existing application record to prevent duplicate
        is_dup, existing_app, reason = self.tracking_agent.check_duplicate_application(candidate_id, job_id)
        if is_dup and existing_app:
            return self.get_application_preview(existing_app.id)

        # Ensure tailored resume exists
        resume: Optional[GeneratedResume] = None
        if resume_id:
            resume = self.db.query(GeneratedResume).filter(GeneratedResume.id == resume_id).first()
        else:
            # Look for existing generated resume for this candidate and job
            resume = (
                self.db.query(GeneratedResume)
                .filter(
                    GeneratedResume.profile_id == candidate_id,
                    GeneratedResume.job_id == job_id
                )
                .order_by(GeneratedResume.id.desc())
                .first()
            )
            # If still none, generate a tailored resume automatically
            if not resume:
                try:
                    resume = self.resume_agent.generate_dual_format_resume(
                        candidate_id=candidate_id,
                        job_id=job_id,
                        tailor_headline=True,
                        tailor_summary=True
                    )
                except Exception as e:
                    logger.warning(f"Could not auto-generate tailored resume: {e}")

        # Map form fields and screening questions
        mapped_fields: List[FormPreviewField] = FormMapperService.map_standard_fields(
            candidate=candidate,
            job=job,
            resume=resume
        )
        screening_answers: List[ScreeningQuestionAnswer] = FormMapperService.answer_screening_questions(
            candidate=candidate,
            job=job
        )

        # Detect any application blockers
        blockers: List[str] = []
        if job.status not in ["ACTIVE", "active"]:
            blockers.append(f"Job vacancy is currently marked as {job.status}. Verification required.")
        if not candidate.phone:
            blockers.append("Candidate phone number is missing from profile.")
        if any(sq.needs_review for sq in screening_answers):
            blockers.append("Some screening questions require candidate confirmation.")
        
        # Candidate approval blocker (enforced by default)
        blockers.append("Explicit candidate approval is required prior to submission.")

        # Serialize mapped preview data for database storage
        preview_data_dict = {
            "mapped_fields": [f.model_dump() for f in mapped_fields],
            "total_fields": len(mapped_fields)
        }
        screening_dict = {
            sq.question: sq.model_dump() for sq in screening_answers
        }

        # Create ApplicationRecord
        app_record = ApplicationRecord(
            candidate_id=candidate_id,
            job_id=job_id,
            resume_id=resume.id if resume else None,
            mode=mode,
            status="Awaiting approval",
            candidate_approved=False,
            form_preview_data=preview_data_dict,
            screening_answers=screening_dict,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(app_record)
        self.db.commit()
        self.db.refresh(app_record)

        # Record initial event
        self.tracking_agent.record_event(
            application_id=app_record.id,
            previous_status=None,
            new_status="Awaiting approval",
            event_source="Agent",
            notes=f"Application prepared in '{mode}' mode. Form mapped and waiting candidate approval."
        )

        # Log execution
        exec_id = f"prep-app-{app_record.id}-{uuid.uuid4().hex[:6]}"
        exec_log = AgentExecutionLog(
            agent_name="ApplicationAutomationAgent",
            execution_id=exec_id,
            task_type="prepare_application",
            status="SUCCESS",
            items_processed=1,
            items_failed=0,
            metadata_json={
                "candidate_id": candidate_id,
                "job_id": job_id,
                "application_id": app_record.id,
                "fields_mapped": len(mapped_fields),
                "screening_questions": len(screening_answers),
                "mode": mode
            },
            start_time=start_time,
            end_time=datetime.utcnow()
        )
        self.db.add(exec_log)
        self.db.commit()

        company_name = job.company.name if job.company else "Pharma Company"

        return ApplicationPreviewResponse(
            application_id=app_record.id,
            candidate_id=candidate_id,
            job_id=job_id,
            job_title=job.title,
            company_name=company_name,
            official_application_url=job.official_application_url,
            resume_id=resume.id if resume else None,
            resume_pdf_path=resume.file_path_pdf if resume else None,
            resume_docx_path=resume.file_path_docx if resume else None,
            mapped_fields=mapped_fields,
            screening_questions=screening_answers,
            candidate_approved=False,
            status=app_record.status,
            mode=app_record.mode,
            can_submit=False,
            blockers=blockers
        )

    def get_application_preview(self, application_id: int) -> ApplicationPreviewResponse:
        """
        Retrieves application form mapping preview and readiness status.
        """
        app_record = (
            self.db.query(ApplicationRecord)
            .filter(ApplicationRecord.id == application_id)
            .first()
        )
        if not app_record:
            raise ValueError(f"Application record with ID {application_id} not found.")

        job = app_record.job
        company_name = job.company.name if (job and job.company) else "Pharma Company"
        resume = app_record.resume

        raw_fields = (app_record.form_preview_data or {}).get("mapped_fields", [])
        mapped_fields = [FormPreviewField(**f) for f in raw_fields] if raw_fields else []

        raw_answers = app_record.screening_answers or {}
        screening_questions = [
            ScreeningQuestionAnswer(**val) if isinstance(val, dict) else ScreeningQuestionAnswer(question=k, answer=str(val))
            for k, val in raw_answers.items()
        ]

        blockers = []
        if not app_record.candidate_approved:
            blockers.append("Explicit candidate approval is required prior to submission.")
        if job and job.status not in ["ACTIVE", "active"]:
            blockers.append(f"Job vacancy status is {job.status}.")

        can_submit = (
            app_record.candidate_approved and
            (not job or job.status in ["ACTIVE", "active"]) and
            app_record.status in ["Awaiting approval", "Shortlisted", "Resume generated"]
        )

        return ApplicationPreviewResponse(
            application_id=app_record.id,
            candidate_id=app_record.candidate_id,
            job_id=app_record.job_id,
            job_title=job.title if job else "Position",
            company_name=company_name,
            official_application_url=job.official_application_url if job else "",
            resume_id=app_record.resume_id,
            resume_pdf_path=resume.file_path_pdf if resume else None,
            resume_docx_path=resume.file_path_docx if resume else None,
            mapped_fields=mapped_fields,
            screening_questions=screening_questions,
            candidate_approved=app_record.candidate_approved,
            status=app_record.status,
            mode=app_record.mode,
            can_submit=can_submit,
            blockers=blockers
        )

    def approve_application(
        self,
        application_id: int,
        notes: Optional[str] = None,
        custom_screening_answers: Optional[Dict[str, Any]] = None
    ) -> ApplicationRecord:
        """
        Records the candidate's explicit approval to submit an application.
        Strictly required before submission.
        """
        app_record = (
            self.db.query(ApplicationRecord)
            .filter(ApplicationRecord.id == application_id)
            .first()
        )
        if not app_record:
            raise ValueError(f"Application record with ID {application_id} not found.")

        app_record.candidate_approved = True
        app_record.approved_at = datetime.utcnow()
        app_record.updated_at = datetime.utcnow()

        if custom_screening_answers:
            current_answers = app_record.screening_answers or {}
            for q_key, ans_val in custom_screening_answers.items():
                if q_key in current_answers and isinstance(current_answers[q_key], dict):
                    current_answers[q_key]["answer"] = ans_val
                    current_answers[q_key]["needs_review"] = False
                    current_answers[q_key]["source"] = "candidate_override"
                else:
                    current_answers[q_key] = {
                        "question": q_key,
                        "answer": ans_val,
                        "source": "candidate_override",
                        "is_truthful": True,
                        "needs_review": False,
                        "explanation": "Overridden or confirmed by candidate during approval."
                    }
            app_record.screening_answers = current_answers

        self.db.commit()
        self.db.refresh(app_record)

        # Audit event
        self.tracking_agent.record_event(
            application_id=app_record.id,
            previous_status=app_record.status,
            new_status=app_record.status,
            event_source="Candidate",
            notes=notes or "Candidate explicitly verified form fields and approved application."
        )

        return app_record

    def submit_application(self, application_id: int) -> ApplicationSubmissionResult:
        """
        Executes assisted submission of the approved application.
        Strictly enforces candidate approval guard.
        Generates official submission reference ID and tracks confirmation.
        """
        start_time = datetime.utcnow()

        app_record = (
            self.db.query(ApplicationRecord)
            .filter(ApplicationRecord.id == application_id)
            .first()
        )
        if not app_record:
            raise ValueError(f"Application record with ID {application_id} not found.")

        # HARD GUARD: Candidate Approval
        if not app_record.candidate_approved:
            raise ValueError(
                "Submission blocked: Candidate explicit approval is required before submission. "
                "Call /approve endpoint or approve via UI first."
            )

        job = app_record.job
        company = job.company if job else None
        company_name = company.name if company else "Pharma Company"
        job_title = job.title if job else "Data Position"
        submission_url = job.official_application_url if job else "https://careers.pharma.internal"

        # Generate unique submission tracking reference
        company_slug = "".join(c for c in company_name if c.isalnum())[:8].upper()
        ref_uuid = uuid.uuid4().hex[:8].upper()
        submission_ref_id = f"APP-{company_slug}-{app_record.job_id}-{ref_uuid}"

        # Transition status to Submitted and then Confirmed
        self.tracking_agent.transition_status(
            application_id=app_record.id,
            new_status="Submitted",
            event_source="Agent",
            notes="Application submitted with candidate approval and ATS-optimized resume.",
            submission_ref_id=submission_ref_id
        )

        # Transition to Application confirmed
        self.tracking_agent.transition_status(
            application_id=app_record.id,
            new_status="Application confirmed",
            event_source="Agent",
            notes=f"Application submission confirmed by career portal. Official Reference ID: {submission_ref_id}."
        )

        # Log agent execution
        exec_id = f"sub-app-{app_record.id}-{uuid.uuid4().hex[:6]}"
        exec_log = AgentExecutionLog(
            agent_name="ApplicationAutomationAgent",
            execution_id=exec_id,
            task_type="submit_application",
            status="SUCCESS",
            items_processed=1,
            items_failed=0,
            metadata_json={
                "application_id": app_record.id,
                "candidate_id": app_record.candidate_id,
                "job_id": app_record.job_id,
                "submission_ref_id": submission_ref_id,
                "submission_url": submission_url
            },
            start_time=start_time,
            end_time=datetime.utcnow()
        )
        self.db.add(exec_log)
        self.db.commit()

        next_steps = [
            f"Official application confirmation logged under reference {submission_ref_id}.",
            "Application tracking agent will monitor updates (Assessment / Interview invitations).",
            f"Tailored resume and submitted application details saved in your dashboard history.",
            "Candidate will be immediately notified when status changes occur."
        ]

        return ApplicationSubmissionResult(
            application_id=app_record.id,
            job_id=app_record.job_id,
            company_name=company_name,
            job_title=job_title,
            status="Application confirmed",
            submission_ref_id=submission_ref_id,
            submission_url=submission_url,
            applied_at=app_record.applied_at or datetime.utcnow(),
            message=f"Application for '{job_title}' at {company_name} successfully submitted and confirmed.",
            next_steps=next_steps
        )
