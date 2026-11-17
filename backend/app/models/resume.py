from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("discovered_jobs.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), default="Tailored ATS Resume")
    file_path_pdf = Column(String(500), nullable=True)
    file_path_docx = Column(String(500), nullable=True)

    keyword_coverage_score = Column(Float, default=0.0)
    matched_keywords = Column(JSON, default=list)       # [{"keyword": "Snowflake", "evidence": "Project"}]
    missing_keywords = Column(JSON, default=list)       # [{"keyword": "Tableau", "evidence": "None"}]
    
    # Snapshot of truthful customized content
    tailored_headline = Column(String(255), nullable=True)
    tailored_summary = Column(Text, nullable=True)
    selected_projects = Column(JSON, default=list)
    selected_skills = Column(JSON, default=list)

    is_approved_by_user = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate_profile = relationship("CandidateProfile", back_populates="generated_resumes")
    job = relationship("DiscoveredJob", back_populates="generated_resumes")
    applications = relationship("ApplicationRecord", back_populates="resume")

