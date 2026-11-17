from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SkillMatchItem(BaseModel):
    skill: str
    candidate_evidence: Optional[str] = None
    status: str = "Matched"  # Matched, Partial, Missing
    is_mandatory: bool = True
    related_skill: Optional[str] = None


class JobMatchScoreBreakdown(BaseModel):
    technical_skills_score: float  # 30%
    experience_score: float        # 20%
    education_score: float         # 15%
    responsibility_score: float    # 15%
    industry_score: float          # 10%
    location_score: float          # 10%


class JobMatchResultResponse(BaseModel):
    id: int
    job_id: int
    profile_id: int
    overall_score: float
    eligibility_label: str  # Excellent match, Strong match, Good match, Partial match, Low match
    is_hard_eligible: bool
    
    score_breakdown: JobMatchScoreBreakdown
    matched_skills: List[Dict[str, Any]] = []
    partially_matched_skills: List[Dict[str, Any]] = []
    missing_skills: List[Dict[str, Any]] = []
    rejection_reasons: List[str] = []
    recommended_action: str
    evaluated_at: datetime

    # Attached Job Overview
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_industry: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    work_mode: Optional[str] = None
    official_application_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BatchMatchRequest(BaseModel):
    min_score_filter: Optional[float] = None
    category_filter: Optional[str] = None
    freshers_only: bool = False
    re_evaluate: bool = False


class BatchMatchResponse(BaseModel):
    total_jobs_evaluated: int
    eligible_jobs_count: int
    strong_matches_count: int
    top_matches: List[JobMatchResultResponse]

