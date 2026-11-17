from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class DiscoveredJob(Base):
    __tablename__ = "discovered_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_uid = Column(String(128), unique=True, index=True, nullable=False)  # Canonical hash for deduplication
    
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(Integer, ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), index=True, nullable=False)
    req_id = Column(String(100), index=True, nullable=True)  # Requisition ID
    category = Column(String(100), index=True, default="Data Engineering")  
    # Data Engineering, Data Analytics, AI/ML, Database/SQL, Clinical Data, Pharma IT/CSV, Other Technical

    location = Column(String(150), default="India")
    city = Column(String(100), index=True, default="Hyderabad")
    work_mode = Column(String(50), default="Hybrid")  # Onsite, Hybrid, Remote
    employment_type = Column(String(50), default="Full-time")  # Full-time, Internship, Trainee, Contract

    min_experience = Column(Float, default=0.0)  # in years, 0.0 allows Freshers
    max_experience = Column(Float, nullable=True)

    education_requirements = Column(String(255), nullable=True)  # B.Tech / M.Sc / MCA
    required_certifications = Column(JSON, default=list)

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="INR")
    salary_disclosed = Column(Boolean, default=False)

    description = Column(Text, nullable=False)
    official_application_url = Column(String(1000), nullable=False)
    canonical_url = Column(String(1000), nullable=False)
    
    posted_date = Column(DateTime, nullable=True)
    application_deadline = Column(DateTime, nullable=True)

    # Status must be one of: ACTIVE, EXPIRED, CLOSED, ON_HOLD, UNKNOWN
    status = Column(String(50), index=True, default="ACTIVE")
    verification_notes = Column(Text, nullable=True)

    first_discovered_at = Column(DateTime, default=datetime.utcnow)
    last_verified_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    source = relationship("JobSource", back_populates="discovered_jobs")
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    match_results = relationship("JobMatchResult", back_populates="job", cascade="all, delete-orphan")
    generated_resumes = relationship("GeneratedResume", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("ApplicationRecord", back_populates="job", cascade="all, delete-orphan")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("discovered_jobs.id", ondelete="CASCADE"), nullable=False)
    req_type = Column(String(50), default="Mandatory")  # Mandatory, Preferred, Trainable
    category = Column(String(50), default="Technical")  # Education, Experience, Certification, Domain, SoftSkill
    description = Column(Text, nullable=False)

    # Relationships
    job = relationship("DiscoveredJob", back_populates="requirements")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("discovered_jobs.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), index=True, nullable=False)
    is_mandatory = Column(Boolean, default=True)
    skill_category = Column(String(50), default="Programming")  # Programming, Database, Cloud, BI, Domain, Tool

    # Relationships
    job = relationship("DiscoveredJob", back_populates="skills")

