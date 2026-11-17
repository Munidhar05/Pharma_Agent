from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class KeywordCoverageItem(BaseModel):
    keyword: str
    candidate_evidence: Optional[str] = None
    status: str = "Matched"  # Matched, Missing
    importance: str = "High"  # High, Medium


class KeywordCoverageReport(BaseModel):
    total_keywords_found: int
    matched_count: int
    missing_count: int
    coverage_percentage: float
    items: List[KeywordCoverageItem]


class TailoredResumeContent(BaseModel):
    headline: str
    summary: str
    selected_skills: List[str]
    selected_projects: List[Dict[str, Any]]
    education: List[Dict[str, Any]]


class GenerateResumeRequest(BaseModel):
    job_id: int
    custom_headline: Optional[str] = None
    custom_summary: Optional[str] = None


class GeneratedResumeResponse(BaseModel):
    id: int
    profile_id: int
    job_id: int
    title: str
    file_path_pdf: Optional[str] = None
    file_path_docx: Optional[str] = None
    keyword_coverage_score: float
    matched_keywords: List[Dict[str, Any]] = []
    missing_keywords: List[Dict[str, Any]] = []
    tailored_headline: Optional[str] = None
    tailored_summary: Optional[str] = None
    is_approved_by_user: bool = False
    generated_at: datetime
    updated_at: datetime

    # Download URLs
    pdf_download_url: Optional[str] = None
    docx_download_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
