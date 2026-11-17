import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import Company, CompanyCareerSource, JobSource, DiscoveredJob
from backend.app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyDetailResponse,
    CompanyCareerSourceCreate,
    CompanyCareerSourceResponse,
    JobSourceResponse,
    CompanyDiscoveryQuery,
    CompanyDiscoveryResult
)
from backend.app.services.career_discovery import CareerDiscoveryService
from backend.app.agents.company_discovery import CompanyDiscoveryAgent

router = APIRouter(prefix="/companies", tags=["Companies & Career Sources"])


@router.get("", response_model=List[CompanyResponse])
def list_companies(
    db: Session = Depends(get_db),
    industry: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """List pharmaceutical, biotechnology, CRO, and life science companies in India."""
    # Ensure primitive types if invoked directly or with Query objects
    if hasattr(industry, "default"):
        industry = industry.default
    if hasattr(search, "default"):
        search = search.default
    if hasattr(is_active, "default"):
        is_active = is_active.default
    if hasattr(skip, "default"):
        skip = skip.default
    if hasattr(limit, "default"):
        limit = limit.default

    query = db.query(Company)

    if industry:
        query = query.filter(Company.industry_category.ilike(f"%{industry}%"))
    if search:
        query = query.filter(
            (Company.name.ilike(f"%{search}%")) |
            (Company.hq_location.ilike(f"%{search}%")) |
            (Company.description.ilike(f"%{search}%"))
        )
    if isinstance(is_active, bool):
        query = query.filter(Company.is_active == is_active)

    return query.order_by(Company.name.asc()).offset(int(skip)).limit(int(limit)).all()


@router.get("/stats/summary")
def get_company_stats(db: Session = Depends(get_db)):
    """Return aggregated industry metrics of all discovered companies."""
    total = db.query(Company).count()
    active = db.query(Company).filter(Company.is_active == True).count()
    
    breakdown = db.query(
        Company.industry_category,
        func.count(Company.id)
    ).group_by(Company.industry_category).all()

    career_sources_count = db.query(CompanyCareerSource).count()

    return {
        "total_companies": total,
        "active_companies": active,
        "total_career_sources": career_sources_count,
        "industry_breakdown": {cat: count for cat, count in breakdown}
    }


@router.get("/{company_id}", response_model=CompanyDetailResponse)
def get_company_detail(company_id: int, db: Session = Depends(get_db)):
    """Retrieve full company details, career sources, and total active job count."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    active_jobs_count = db.query(DiscoveredJob).filter(
        DiscoveredJob.company_id == company.id,
        DiscoveredJob.status == "ACTIVE"
    ).count()

    return CompanyDetailResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        industry_category=company.industry_category,
        website=company.website,
        careers_url=company.careers_url,
        hq_location=company.hq_location,
        description=company.description,
        is_active=company.is_active,
        created_at=company.created_at,
        updated_at=company.updated_at,
        career_sources=[CompanyCareerSourceResponse.model_validate(cs) for cs in company.career_sources],
        total_active_jobs=active_jobs_count
    )


@router.post("", response_model=CompanyDetailResponse, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    """
    Register a new pharmaceutical company.
    Automatically analyzes career URL to detect ATS platform and configure career source.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", payload.name.lower()).strip("-")
    existing = db.query(Company).filter(
        (Company.slug == slug) | (Company.name.ilike(payload.name))
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Company '{payload.name}' already exists.")

    company = Company(
        name=payload.name,
        slug=slug,
        industry_category=payload.industry_category,
        website=payload.website,
        careers_url=payload.careers_url,
        hq_location=payload.hq_location,
        description=payload.description,
        is_active=payload.is_active
    )
    db.add(company)
    db.flush()

    # Automatically detect ATS if career URL is supplied
    if payload.careers_url:
        career_info = CareerDiscoveryService.analyze_company_career(payload.name, payload.careers_url)
        career_source = CompanyCareerSource(
            company_id=company.id,
            source_type=career_info["source_type"],
            base_url=career_info["career_url"],
            career_url=career_info["career_url"],
            api_endpoint=career_info["api_endpoint"],
            is_active=True
        )
        db.add(career_source)

    db.commit()
    db.refresh(company)
    return get_company_detail(company_id=company.id, db=db)


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    """Update company metadata."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(company, field, val)

    db.commit()
    db.refresh(company)
    return company


@router.post("/{company_id}/career-sources", response_model=CompanyCareerSourceResponse)
def add_company_career_source(
    company_id: int,
    payload: CompanyCareerSourceCreate,
    db: Session = Depends(get_db)
):
    """Add or attach an ATS career source endpoint to a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    source = CompanyCareerSource(
        company_id=company.id,
        source_type=payload.source_type,
        base_url=payload.base_url,
        career_url=payload.career_url,
        api_endpoint=payload.api_endpoint,
        scrape_config=payload.scrape_config,
        is_active=payload.is_active
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/discover", response_model=CompanyDiscoveryResult)
def trigger_company_discovery(
    query: CompanyDiscoveryQuery = CompanyDiscoveryQuery(),
    db: Session = Depends(get_db)
):
    """
    Trigger Agent 1 (Company Discovery Agent) to discover new companies,
    validate career portals, and register ATS endpoints.
    """
    agent = CompanyDiscoveryAgent(db=db)
    result = agent.run_discovery_cycle(
        keyword=query.keyword,
        industry_category=query.industry_category,
        auto_detect_ats=query.auto_detect_ats
    )

    return CompanyDiscoveryResult(
        total_companies_evaluated=result["items_processed"],
        new_companies_added=result["new_companies_added"],
        career_sources_detected=result["sources_detected"],
        companies=[CompanyResponse.model_validate(c) for c in result["new_companies"]],
        execution_id=result["execution_id"]
    )


@router.get("/sources/registry", response_model=List[JobSourceResponse])
def list_global_job_sources(db: Session = Depends(get_db)):
    """List all registered external job boards and ATS platforms (LinkedIn, Naukri, Indeed, etc.)."""
    return db.query(JobSource).order_by(JobSource.id.asc()).all()
