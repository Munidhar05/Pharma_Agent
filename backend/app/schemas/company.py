from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CompanyCareerSourceBase(BaseModel):
    source_type: str = Field(..., description="Workday, Greenhouse, Lever, Taleo, Direct, RSS")
    base_url: str
    career_url: str
    api_endpoint: Optional[str] = None
    scrape_config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class CompanyCareerSourceCreate(CompanyCareerSourceBase):
    pass


class CompanyCareerSourceResponse(CompanyCareerSourceBase):
    id: int
    company_id: int
    last_scraped_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyBase(BaseModel):
    name: str
    slug: str
    industry_category: str = Field(
        ...,
        description="Indian Pharma, Global Pharma, CRO & Clinical Research, Biotech & Life Sciences, Pharma Tech"
    )
    website: Optional[str] = None
    careers_url: Optional[str] = None
    hq_location: str = "India"
    description: Optional[str] = None
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry_category: Optional[str] = None
    website: Optional[str] = None
    careers_url: Optional[str] = None
    hq_location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyDetailResponse(CompanyResponse):
    career_sources: List[CompanyCareerSourceResponse] = []
    total_active_jobs: int = 0

    model_config = ConfigDict(from_attributes=True)


class JobSourceBase(BaseModel):
    name: str
    source_type: str
    base_url: str
    rate_limit_per_min: int = 30
    is_active: bool = True


class JobSourceCreate(JobSourceBase):
    pass


class JobSourceResponse(JobSourceBase):
    id: int
    last_crawled_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyDiscoveryQuery(BaseModel):
    keyword: Optional[str] = None
    industry_category: Optional[str] = None
    auto_detect_ats: bool = True


class CompanyDiscoveryResult(BaseModel):
    total_companies_evaluated: int
    new_companies_added: int
    career_sources_detected: int
    companies: List[CompanyResponse]
    execution_id: str
