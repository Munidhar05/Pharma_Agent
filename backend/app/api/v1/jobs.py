from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import DiscoveredJob, Company, JobRequirement, JobSkill
from backend.app.schemas.job import (
    DiscoveredJobCreate,
    DiscoveredJobUpdate,
    DiscoveredJobResponse,
    DiscoveredJobDetailResponse,
    JobRequirementResponse,
    JobSkillResponse,
    JobSearchQuery,
    JobSearchResult,
    JobVerificationResult
)
from backend.app.agents.job_search import JobSearchAgent
from backend.app.agents.job_verification import JobVerificationAgent
from backend.app.agents.job_extraction import JobExtractionAgent
from backend.app.services.job_extractor import JobExtractorService

router = APIRouter(prefix="/jobs", tags=["Discovered Jobs"])


def _to_job_response(job: DiscoveredJob) -> DiscoveredJobResponse:
    """Helper to convert DiscoveredJob to response schema with company details."""
    return DiscoveredJobResponse(
        id=job.id,
        job_uid=job.job_uid,
        company_id=job.company_id,
        source_id=job.source_id,
        company_name=job.company.name if job.company else None,
        company_industry=job.company.industry_category if job.company else None,
        title=job.title,
        req_id=job.req_id,
        category=job.category,
        location=job.location,
        city=job.city,
        work_mode=job.work_mode,
        employment_type=job.employment_type,
        min_experience=job.min_experience,
        max_experience=job.max_experience,
        education_requirements=job.education_requirements,
        required_certifications=job.required_certifications or [],
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_disclosed=job.salary_disclosed,
        description=job.description,
        official_application_url=job.official_application_url,
        canonical_url=job.canonical_url,
        posted_date=job.posted_date,
        application_deadline=job.application_deadline,
        status=job.status,
        first_discovered_at=job.first_discovered_at,
        last_verified_at=job.last_verified_at,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.get("", response_model=List[DiscoveredJobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    city: Optional[str] = None,
    company_id: Optional[int] = None,
    work_mode: Optional[str] = None,
    status: Optional[str] = "ACTIVE",
    max_experience: Optional[float] = None,
    freshers_only: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Search and filter discovered pharmaceutical data jobs across India.
    Filters by technical category, Indian cities, work mode, and experience range.
    """
    if hasattr(category, "default"):
        category = category.default
    if hasattr(city, "default"):
        city = city.default
    if hasattr(company_id, "default"):
        company_id = company_id.default
    if hasattr(work_mode, "default"):
        work_mode = work_mode.default
    if hasattr(status, "default"):
        status = status.default
    if hasattr(max_experience, "default"):
        max_experience = max_experience.default
    if hasattr(freshers_only, "default"):
        freshers_only = freshers_only.default
    if hasattr(search, "default"):
        search = search.default
    if hasattr(skip, "default"):
        skip = skip.default
    if hasattr(limit, "default"):
        limit = limit.default

    query = db.query(DiscoveredJob)

    if status:
        query = query.filter(DiscoveredJob.status == status)
    if category:
        query = query.filter(DiscoveredJob.category.ilike(f"%{category}%"))
    if city:
        query = query.filter(DiscoveredJob.city.ilike(f"%{city}%"))
    if company_id:
        query = query.filter(DiscoveredJob.company_id == company_id)
    if work_mode:
        query = query.filter(DiscoveredJob.work_mode.ilike(f"%{work_mode}%"))
    if freshers_only:
        query = query.filter(DiscoveredJob.min_experience <= 0.0)
    elif max_experience is not None:
        query = query.filter(DiscoveredJob.min_experience <= max_experience)
    if search:
        query = query.filter(
            (DiscoveredJob.title.ilike(f"%{search}%")) |
            (DiscoveredJob.description.ilike(f"%{search}%")) |
            (DiscoveredJob.city.ilike(f"%{search}%"))
        )

    jobs = query.order_by(DiscoveredJob.first_discovered_at.desc()).offset(int(skip)).limit(int(limit)).all()
    return [_to_job_response(j) for j in jobs]


@router.get("/stats/summary")
def get_job_stats(db: Session = Depends(get_db)):
    """Summary of discovered job counts by status, technical category, top cities, and companies."""
    total = db.query(DiscoveredJob).count()
    active = db.query(DiscoveredJob).filter(DiscoveredJob.status == "ACTIVE").count()
    freshers = db.query(DiscoveredJob).filter(DiscoveredJob.min_experience <= 0.0).count()

    category_counts = db.query(
        DiscoveredJob.category,
        func.count(DiscoveredJob.id)
    ).group_by(DiscoveredJob.category).all()

    city_counts = db.query(
        DiscoveredJob.city,
        func.count(DiscoveredJob.id)
    ).group_by(DiscoveredJob.city).order_by(func.count(DiscoveredJob.id).desc()).limit(10).all()

    return {
        "total_jobs_discovered": total,
        "active_jobs": active,
        "fresher_friendly_jobs": freshers,
        "categories": {cat: count for cat, count in category_counts},
        "top_cities": {c: count for c, count in city_counts}
    }


@router.get("/{job_id}", response_model=DiscoveredJobDetailResponse)
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    """Retrieve complete vacancy details with mandatory/preferred requirements and skills."""
    job = db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found.")

    res = _to_job_response(job)
    return DiscoveredJobDetailResponse(
        **res.model_dump(),
        requirements=[JobRequirementResponse.model_validate(r) for r in job.requirements],
        skills=[JobSkillResponse.model_validate(s) for s in job.skills],
        company_website=job.company.website if job.company else None,
        verification_notes=job.verification_notes
    )


@router.post("", response_model=DiscoveredJobDetailResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: DiscoveredJobCreate, db: Session = Depends(get_db)):
    """Manually add or ingest a job vacancy."""
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    extractor = JobExtractionAgent(db=db)
    raw_data = payload.model_dump()
    discovered_job = extractor.extract_and_structure_job(
        raw_job=raw_data,
        company=company,
        source_id=payload.source_id
    )

    db.add(discovered_job)
    db.commit()
    db.refresh(discovered_job)
    return get_job_detail(job_id=discovered_job.id, db=db)


@router.put("/{job_id}", response_model=DiscoveredJobResponse)
def update_job(job_id: int, payload: DiscoveredJobUpdate, db: Session = Depends(get_db)):
    """Update job attributes or change status."""
    job = db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(job, field, val)

    db.commit()
    db.refresh(job)
    return _to_job_response(job)


@router.post("/search", response_model=JobSearchResult)
def trigger_job_search(
    query: JobSearchQuery = JobSearchQuery(),
    db: Session = Depends(get_db)
):
    """
    Trigger Agent 2 (Job Search Agent) to execute an autonomous discovery cycle
    across pharmaceutical career portals and external job feeds.
    """
    agent = JobSearchAgent(db=db)
    result = agent.execute_search(
        category=query.category,
        city=query.city,
        max_experience=query.max_experience,
        freshers_only=query.freshers_only,
        company_id=query.company_id
    )

    return JobSearchResult(
        execution_id=result["execution_id"],
        total_sources_probed=result["total_sources_probed"],
        new_jobs_discovered=result["new_jobs_discovered"],
        jobs_updated=result["jobs_updated"],
        duplicates_skipped=result["duplicates_skipped"],
        discovered_jobs=[_to_job_response(j) for j in result["discovered_jobs"]]
    )


@router.post("/{job_id}/verify", response_model=JobVerificationResult)
def verify_single_job(job_id: int, db: Session = Depends(get_db)):
    """Trigger Agent 4 (Job Verification Agent) to verify a specific job URL and status."""
    job = db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    verifier = JobVerificationAgent(db=db)
    res = verifier.verify_job_status(job)

    return JobVerificationResult(
        job_id=res["job_id"],
        previous_status=res["previous_status"],
        current_status=res["current_status"],
        is_active=res["is_active"],
        verification_notes=res["verification_notes"],
        verified_at=res["verified_at"]
    )


@router.post("/verify-all")
def verify_all_stale_jobs(db: Session = Depends(get_db)):
    """Trigger Agent 4 (Job Verification Agent) to verify all stale active jobs."""
    verifier = JobVerificationAgent(db=db)
    res = verifier.verify_stale_jobs()
    return res

