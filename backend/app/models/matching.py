from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class JobMatchResult(Base):
    __tablename__ = "job_match_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("discovered_jobs.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    # Dimensional Scores (0 - 100)
    overall_score = Column(Float, index=True, nullable=False)
    skills_score = Column(Float, default=0.0)          # 30% weight
    experience_score = Column(Float, default=0.0)      # 20% weight
    education_score = Column(Float, default=0.0)       # 15% weight
    responsibility_score = Column(Float, default=0.0)  # 15% weight
    industry_score = Column(Float, default=0.0)        # 10% weight
    location_score = Column(Float, default=0.0)        # 10% weight

    # Categorical label: "Excellent match", "Strong match", "Good match", "Partial match", "Low match"
    eligibility_label = Column(String(50), index=True, nullable=False)
    
    # Hard eligibility check (e.g. false if missing mandatory degree or experience threshold)
    is_hard_eligible = Column(Boolean, default=True)
    
    # Detailed Skill Breakdown
    matched_skills = Column(JSON, default=list)             # [{"skill": "Python", "candidate_evidence": "Projects"}]
    partially_matched_skills = Column(JSON, default=list)   # [{"skill": "Spark", "candidate_evidence": "PySpark"}]
    missing_skills = Column(JSON, default=list)             # [{"skill": "AWS Glue", "is_mandatory": false}]
    rejection_reasons = Column(JSON, default=list)          # ["Experience mismatch: requires 3 yrs, candidate has 0 yrs"]
    
    recommended_action = Column(String(255), default="Review and Apply")
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("DiscoveredJob", back_populates="match_results")
    candidate_profile = relationship("CandidateProfile", back_populates="match_results")

