from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# Skill Schemas
class CandidateSkillBase(BaseModel):
    name: str
    category: str = "Programming"  # Programming, Database, Cloud, BI/Visualization, Tool, Domain
    proficiency: str = "Intermediate"
    years_experience: float = Field(default=1.0, ge=0.0)
    verified: bool = True


class CandidateSkillCreate(CandidateSkillBase):
    pass


class CandidateSkillResponse(CandidateSkillBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# Education Schemas
class CandidateEducationBase(BaseModel):
    degree: str
    field_of_study: str
    institution: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa_or_percentage: Optional[float] = None
    is_highest: bool = True


class CandidateEducationCreate(CandidateEducationBase):
    pass


class CandidateEducationResponse(CandidateEducationBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# Experience Schemas
class CandidateExperienceBase(BaseModel):
    company_name: str
    job_title: str
    employment_type: str = "Internship"
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False
    description: Optional[str] = None
    technologies_used: List[str] = Field(default_factory=list)


class CandidateExperienceCreate(CandidateExperienceBase):
    pass


class CandidateExperienceResponse(CandidateExperienceBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# Project Schemas
class CandidateProjectBase(BaseModel):
    title: str
    role: str = "Data Engineer"
    domain: str = "Healthcare / Data Engineering"
    description: str
    technologies: List[str] = Field(default_factory=list)
    repo_url: Optional[str] = None
    live_url: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class CandidateProjectCreate(CandidateProjectBase):
    pass


class CandidateProjectResponse(CandidateProjectBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# Resume Schema
class CandidateResumeResponse(BaseModel):
    id: int
    original_filename: str
    file_size_bytes: int
    file_type: str
    is_primary: bool
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Profile Schemas
class CandidateProfileUpdate(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    total_experience_years: Optional[float] = None
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    notice_period_days: Optional[int] = None
    current_location: Optional[str] = None
    willing_to_relocate: Optional[bool] = None
    employment_preferences: Optional[List[str]] = None


class CandidateProfileDetailResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    total_experience_years: float = 0.0
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    notice_period_days: int = 0
    current_location: str = "Hyderabad"
    willing_to_relocate: bool = True
    employment_preferences: List[str] = []
    verified_by_candidate: bool = False
    
    skills: List[CandidateSkillResponse] = []
    education: List[CandidateEducationResponse] = []
    experience: List[CandidateExperienceResponse] = []
    projects: List[CandidateProjectResponse] = []
    resumes: List[CandidateResumeResponse] = []
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    message: str
    resume_id: int
    filename: str
    file_type: str
    extracted_data_summary: Dict[str, Any]
    profile_completeness_score: int
    verification_required: bool = True
