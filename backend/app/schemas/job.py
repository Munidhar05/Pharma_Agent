from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# Job Requirement Schemas
class JobRequirementBase(BaseModel):
    req_type: str = "Mandatory"  # Mandatory, Preferred, Trainable
    category: str = "Technical"  # Education, Experience, Certification, Domain, SoftSkill
    description: str


class JobRequirementCreate(JobRequirementBase):
    pass


class JobRequirementResponse(JobRequirementBase):
    id: int
    job_id: int

    model_config = ConfigDict(from_attributes=True)


# Job Skill Schemas
class JobSkillBase(BaseModel):
    skill_name: str
    is_mandatory: bool = True
    skill_category: str = "Programming"  # Programming, Database, Cloud, BI, Domain, Tool


class JobSkillCreate(JobSkillBase):
    pass


class JobSkillResponse(JobSkillBase):
    id: int
    job_id: int

    model_config = ConfigDict(from_attributes=True)


# Discovered Job Schemas
class DiscoveredJobBase(BaseModel):
    title: str
    req_id: Optional[str] = None
    category: str = "Data Engineering"  # Data Engineering, Data Analytics, AI/ML, Database/SQL, Clinical Data, Pharma IT/CSV, Other Technical
    location: str = "India"
    city: str = "Hyderabad"
    work_mode: str = "Hybrid"  # Onsite, Hybrid, Remote
    employment_type: str = "Full-time"  # Full-time, Internship, Trainee, Contract
    min_experience: float = 0.0
    max_experience: Optional[float] = None
    education_requirements: Optional[str] = None
    required_certifications: List[str] = Field(default_factory=list)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "INR"
    salary_disclosed: bool = False
    description: str
    official_application_url: str
    canonical_url: str
    status: str = "ACTIVE"  # ACTIVE, EXPIRED, CLOSED, ON_HOLD, UNKNOWN


class DiscoveredJobCreate(DiscoveredJobBase):
    company_id: int
    source_id: Optional[int] = None
    job_uid: Optional[str] = None  # Auto-generated if omitted
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None


class DiscoveredJobUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    work_mode: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None
    verification_notes: Optional[str] = None


class DiscoveredJobResponse(DiscoveredJobBase):
    id: int
    job_uid: str
    company_id: int
    source_id: Optional[int] = None
    company_name: Optional[str] = None
    company_industry: Optional[str] = None
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    first_discovered_at: datetime
    last_verified_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscoveredJobDetailResponse(DiscoveredJobResponse):
    requirements: List[JobRequirementResponse] = []
    skills: List[JobSkillResponse] = []
    company_website: Optional[str] = None
    verification_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobSearchQuery(BaseModel):
    category: Optional[str] = None
    city: Optional[str] = None
    max_experience: Optional[float] = None
    freshers_only: bool = False
    company_id: Optional[int] = None
    source_type: Optional[str] = None  # Workday, Greenhouse, Lever, All


class JobSearchResult(BaseModel):
    execution_id: str
    total_sources_probed: int
    new_jobs_discovered: int
    jobs_updated: int
    duplicates_skipped: int
    discovered_jobs: List[DiscoveredJobResponse]


class JobVerificationResult(BaseModel):
    job_id: int
    previous_status: str
    current_status: str
    is_active: bool
    verification_notes: str
    verified_at: datetime

