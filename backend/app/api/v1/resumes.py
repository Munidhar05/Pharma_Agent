import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import CandidateProfile, DiscoveredJob, GeneratedResume
from backend.app.schemas.resume import (
    GeneratedResumeResponse,
    GenerateResumeRequest,
    KeywordCoverageReport
)
from backend.app.api.v1.candidate import get_current_candidate_profile
from backend.app.agents.resume_generation import ResumeGenerationAgent
from backend.app.agents.ats_optimization import ATSOptimizationAgent

router = APIRouter(prefix="/resumes", tags=["Tailored ATS Resumes"])


def _to_resume_response(rec: GeneratedResume) -> GeneratedResumeResponse:
    """Helper to convert GeneratedResume to response schema with download links."""
    return GeneratedResumeResponse(
        id=rec.id,
        profile_id=rec.profile_id,
        job_id=rec.job_id,
        title=rec.title,
        file_path_pdf=rec.file_path_pdf,
        file_path_docx=rec.file_path_docx,
        keyword_coverage_score=rec.keyword_coverage_score,
        matched_keywords=rec.matched_keywords or [],
        missing_keywords=rec.missing_keywords or [],
        tailored_headline=rec.tailored_headline,
        tailored_summary=rec.tailored_summary,
        is_approved_by_user=rec.is_approved_by_user,
        generated_at=rec.generated_at,
        updated_at=rec.updated_at,
        pdf_download_url=f"/api/v1/resumes/{rec.id}/download/pdf",
        docx_download_url=f"/api/v1/resumes/{rec.id}/download/docx"
    )


@router.post("/generate/{job_id}", response_model=GeneratedResumeResponse, status_code=status.HTTP_201_CREATED)
def generate_resume_for_job(
    job_id: int,
    payload: Optional[GenerateResumeRequest] = None,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """
    Generate an ATS-compliant tailored resume in PDF and DOCX formats for a specific vacancy.
    Optimizes keywords truthfully using candidate's verified background.
    """
    job = db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found.")

    agent = ResumeGenerationAgent(db=db)
    resume_rec = agent.generate_tailored_resume(
        candidate=profile,
        job=job,
        custom_headline=payload.custom_headline if payload else None,
        custom_summary=payload.custom_summary if payload else None
    )

    return _to_resume_response(resume_rec)


@router.get("/job/{job_id}", response_model=GeneratedResumeResponse)
def get_resume_by_job(
    job_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Retrieve the generated tailored resume for a specific vacancy."""
    rec = db.query(GeneratedResume).filter(
        GeneratedResume.profile_id == profile.id,
        GeneratedResume.job_id == job_id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="No tailored resume generated yet for this job.")

    return _to_resume_response(rec)


@router.get("/{resume_id}", response_model=GeneratedResumeResponse)
def get_resume_detail(
    resume_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Retrieve details and keyword coverage score of a generated resume."""
    rec = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.profile_id == profile.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Generated resume not found.")

    return _to_resume_response(rec)


@router.get("/{resume_id}/coverage", response_model=KeywordCoverageReport)
def get_resume_keyword_coverage(
    resume_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Retrieve the full ATS Keyword Coverage Report comparing resume against job keywords."""
    rec = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.profile_id == profile.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Generated resume not found.")

    job = rec.job
    ats_agent = ATSOptimizationAgent(candidate=profile, job=job)
    return ats_agent.generate_coverage_report()


@router.get("/{resume_id}/download/pdf")
def download_resume_pdf(
    resume_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Download the generated ATS PDF resume."""
    rec = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.profile_id == profile.id
    ).first()

    if not rec or not rec.file_path_pdf or not os.path.exists(rec.file_path_pdf):
        raise HTTPException(status_code=404, detail="PDF resume file not found.")

    filename = os.path.basename(rec.file_path_pdf)
    return FileResponse(
        path=rec.file_path_pdf,
        media_type="application/pdf",
        filename=filename
    )


@router.get("/{resume_id}/download/docx")
def download_resume_docx(
    resume_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Download the generated ATS DOCX resume."""
    rec = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.profile_id == profile.id
    ).first()

    if not rec or not rec.file_path_docx or not os.path.exists(rec.file_path_docx):
        raise HTTPException(status_code=404, detail="DOCX resume file not found.")

    filename = os.path.basename(rec.file_path_docx)
    return FileResponse(
        path=rec.file_path_docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )


@router.post("/{resume_id}/approve", response_model=GeneratedResumeResponse)
def approve_generated_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Candidate explicitly approves the tailored resume for use in applications."""
    rec = db.query(GeneratedResume).filter(
        GeneratedResume.id == resume_id,
        GeneratedResume.profile_id == profile.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Generated resume not found.")

    rec.is_approved_by_user = True
    db.commit()
    db.refresh(rec)
    return _to_resume_response(rec)


@router.get("", response_model=List[GeneratedResumeResponse])
def list_all_generated_resumes(
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """List all generated resumes for candidate."""
    resumes = db.query(GeneratedResume).filter(
        GeneratedResume.profile_id == profile.id
    ).order_by(GeneratedResume.generated_at.desc()).all()

    return [_to_resume_response(r) for r in resumes]

