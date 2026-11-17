from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class FormPreviewField(BaseModel):
    field_name: str
    field_label: str
    field_value: Any
    field_type: str = "text"  # text, email, phone, file, select, radio, textarea
    required: bool = True
    source: str = "candidate_profile"
    confidence: float = 1.0
    requires_candidate_input: bool = False


class ScreeningQuestionAnswer(BaseModel):
    question: str
    answer: Any
    source: str = "candidate_profile"
    is_truthful: bool = True
    needs_review: bool = False
    explanation: str = ""


class ApplicationRecordCreate(BaseModel):
    candidate_id: int
    job_id: int
    resume_id: Optional[int] = None
    mode: Optional[str] = "Assisted application with approval"


class ApplicationApprovalRequest(BaseModel):
    candidate_approved: bool = True
    notes: Optional[str] = None
    custom_screening_answers: Optional[Dict[str, Any]] = None


class ApplicationStatusUpdateRequest(BaseModel):
    new_status: str
    notes: Optional[str] = None
    submission_ref_id: Optional[str] = None
    event_source: Optional[str] = "Candidate"


class ApplicationEventResponse(BaseModel):
    id: int
    application_id: int
    previous_status: Optional[str] = None
    new_status: str
    event_source: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationPreviewResponse(BaseModel):
    application_id: Optional[int] = None
    candidate_id: int
    job_id: int
    job_title: str
    company_name: str
    official_application_url: str
    resume_id: Optional[int] = None
    resume_pdf_path: Optional[str] = None
    resume_docx_path: Optional[str] = None
    mapped_fields: List[FormPreviewField] = []
    screening_questions: List[ScreeningQuestionAnswer] = []
    candidate_approved: bool = False
    status: str = "Awaiting approval"
    mode: str = "Assisted application with approval"
    can_submit: bool = False
    blockers: List[str] = []


class ApplicationSubmissionResult(BaseModel):
    application_id: int
    job_id: int
    company_name: str
    job_title: str
    status: str
    submission_ref_id: Optional[str] = None
    submission_url: str
    applied_at: Optional[datetime] = None
    message: str
    next_steps: List[str] = []


class ApplicationRecordResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    resume_id: Optional[int] = None
    mode: str
    status: str
    candidate_approved: bool
    approved_at: Optional[datetime] = None
    submission_ref_id: Optional[str] = None
    submission_screenshot_path: Optional[str] = None
    form_preview_data: Optional[Dict[str, Any]] = None
    screening_answers: Optional[Dict[str, Any]] = None
    applied_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatsResponse(BaseModel):
    total_applications: int
    awaiting_approval: int
    submitted: int
    confirmed: int
    interviews: int
    assessments: int
    offers: int
    rejections: int
