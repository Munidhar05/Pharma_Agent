from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import CandidateProfile, DiscoveredJob, JobMatchResult, UserPreferences
from backend.app.schemas.matching import (
    JobMatchResultResponse,
    JobMatchScoreBreakdown,
    BatchMatchRequest,
    BatchMatchResponse
)
from backend.app.api.v1.candidate import get_current_candidate_profile
from backend.app.agents.job_matching import JobMatchingAgent

router = APIRouter(prefix="/matching", tags=["Intelligent Job Matching"])


def _to_match_response(match: JobMatchResult) -> JobMatchResultResponse:
    """Helper to convert JobMatchResult model to response schema with attached job info."""
    job = match.job
    return JobMatchResultResponse(
        id=match.id,
        job_id=match.job_id,
        profile_id=match.profile_id,
        overall_score=match.overall_score,
        eligibility_label=match.eligibility_label,
        is_hard_eligible=match.is_hard_eligible,
        score_breakdown=JobMatchScoreBreakdown(
            technical_skills_score=match.skills_score,
            experience_score=match.experience_score,
            education_score=match.education_score,
            responsibility_score=match.responsibility_score,
            industry_score=match.industry_score,
            location_score=match.location_score
        ),
        matched_skills=match.matched_skills or [],
        partially_matched_skills=match.partially_matched_skills or [],
        missing_skills=match.missing_skills or [],
        rejection_reasons=match.rejection_reasons or [],
        recommended_action=match.recommended_action,
        evaluated_at=match.evaluated_at,
        job_title=job.title if job else None,
        company_name=job.company.name if job and job.company else None,
        company_industry=job.company.industry_category if job and job.company else None,
        city=job.city if job else None,
        category=job.category if job else None,
        work_mode=job.work_mode if job else None,
        official_application_url=job.official_application_url if job else None
    )


@router.get("", response_model=List[JobMatchResultResponse])
def get_job_matches(
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile),
    min_score: Optional[float] = None,
    label: Optional[str] = None,
    hard_eligible_only: bool = True,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Retrieve ranked job matches for candidate with multi-dimensional match scores.
    Sorted by overall match score descending.
    """
    if hasattr(min_score, "default"):
        min_score = min_score.default
    if hasattr(label, "default"):
        label = label.default
    if hasattr(hard_eligible_only, "default"):
        hard_eligible_only = hard_eligible_only.default
    if hasattr(category, "default"):
        category = category.default
    if hasattr(skip, "default"):
        skip = skip.default
    if hasattr(limit, "default"):
        limit = limit.default

    query = db.query(JobMatchResult).join(DiscoveredJob).filter(
        JobMatchResult.profile_id == profile.id
    )

    if min_score is not None:
        query = query.filter(JobMatchResult.overall_score >= min_score)
    if label:
        query = query.filter(JobMatchResult.eligibility_label.ilike(f"%{label}%"))
    if hard_eligible_only:
        query = query.filter(JobMatchResult.is_hard_eligible == True)
    if category:
        query = query.filter(DiscoveredJob.category.ilike(f"%{category}%"))

    matches = query.order_by(JobMatchResult.overall_score.desc()).offset(int(skip)).limit(int(limit)).all()
    return [_to_match_response(m) for m in matches]


@router.get("/job/{job_id}", response_model=JobMatchResultResponse)
def get_single_job_match(
    job_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Retrieve detailed matching analysis for a specific job."""
    match = db.query(JobMatchResult).filter(
        JobMatchResult.profile_id == profile.id,
        JobMatchResult.job_id == job_id
    ).first()

    if not match:
        # Evaluate on the fly if not yet evaluated
        job = db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job vacancy not found.")
        agent = JobMatchingAgent(db=db)
        match = agent.evaluate_candidate_for_job(candidate=profile, job=job)

    return _to_match_response(match)


@router.post("/evaluate/{job_id}", response_model=JobMatchResultResponse)
def evaluate_job_match(
    job_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Trigger Agent 6 to evaluate or recalculate match score for a job."""
    job = db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found.")

    agent = JobMatchingAgent(db=db)
    match = agent.evaluate_candidate_for_job(candidate=profile, job=job)
    return _to_match_response(match)


@router.post("/evaluate-all", response_model=BatchMatchResponse)
@router.post("/evaluate-batch", response_model=BatchMatchResponse)
def evaluate_all_jobs(
    payload: BatchMatchRequest = BatchMatchRequest(),
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """
    Trigger Agent 6 (Job Matching Agent) to batch evaluate all active discovered jobs
    against the candidate's verified profile.
    """
    agent = JobMatchingAgent(db=db)
    result = agent.evaluate_all_active_jobs(
        candidate=profile,
        category=payload.category_filter,
        freshers_only=payload.freshers_only
    )

    top_matches = result["matches"]
    if payload.min_score_filter:
        top_matches = [m for m in top_matches if m.overall_score >= payload.min_score_filter]

    return BatchMatchResponse(
        total_jobs_evaluated=result["total_jobs_evaluated"],
        eligible_jobs_count=result["eligible_jobs_count"],
        strong_matches_count=result["strong_matches_count"],
        top_matches=[_to_match_response(m) for m in top_matches[:20]]
    )


@router.get("/top-recommendations", response_model=List[JobMatchResultResponse])
@router.get("/recommendations", response_model=List[JobMatchResultResponse])
def get_top_recommendations(
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile),
    limit: int = 5
):
    """Return top 5 highest matching job opportunities for instant candidate dashboard preview."""
    if hasattr(limit, "default"):
        limit = limit.default

    matches = db.query(JobMatchResult).filter(
        JobMatchResult.profile_id == profile.id,
        JobMatchResult.is_hard_eligible == True
    ).order_by(JobMatchResult.overall_score.desc()).limit(int(limit)).all()

    return [_to_match_response(m) for m in matches]

