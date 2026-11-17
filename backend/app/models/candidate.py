from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    headline = Column(String(255), default="Data Engineer / Healthcare Analytics Professional")
    summary = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    
    total_experience_years = Column(Float, default=0.0)  # 0.0 for Fresher
    current_ctc = Column(Float, nullable=True)
    expected_ctc = Column(Float, nullable=True)
    notice_period_days = Column(Integer, default=0)
    current_location = Column(String(100), default="Hyderabad")
    willing_to_relocate = Column(Boolean, default=True)
    employment_preferences = Column(JSON, default=lambda: ["Full-time", "Hybrid", "Remote"])
    
    verified_by_candidate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="candidate_profile")
    skills = relationship("CandidateSkill", back_populates="profile", cascade="all, delete-orphan")
    education = relationship("CandidateEducation", back_populates="profile", cascade="all, delete-orphan")
    experience = relationship("CandidateExperience", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("CandidateProject", back_populates="profile", cascade="all, delete-orphan")
    resumes = relationship("CandidateResume", back_populates="profile", cascade="all, delete-orphan")
    match_results = relationship("JobMatchResult", back_populates="candidate_profile", cascade="all, delete-orphan")
    generated_resumes = relationship("GeneratedResume", back_populates="candidate_profile", cascade="all, delete-orphan")
    applications = relationship("ApplicationRecord", back_populates="candidate_profile", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), index=True, nullable=False)
    category = Column(String(100), default="Technical")  # Programming, Database, Cloud, BI/Visualization, Tool, Domain
    proficiency = Column(String(50), default="Intermediate")  # Beginner, Intermediate, Advanced, Expert
    years_experience = Column(Float, default=1.0)
    verified = Column(Boolean, default=True)

    # Relationships
    profile = relationship("CandidateProfile", back_populates="skills")


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    degree = Column(String(150), nullable=False)  # B.Tech, M.Sc, etc.
    field_of_study = Column(String(150), nullable=False)  # Computer Science, Biotechnology, etc.
    institution = Column(String(255), nullable=False)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    cgpa_or_percentage = Column(Float, nullable=True)
    is_highest = Column(Boolean, default=True)

    # Relationships
    profile = relationship("CandidateProfile", back_populates="education")


class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(150), nullable=False)
    employment_type = Column(String(50), default="Full-time")  # Full-time, Internship, Contract
    location = Column(String(100), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    technologies_used = Column(JSON, default=list)

    # Relationships
    profile = relationship("CandidateProfile", back_populates="experience")


class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    role = Column(String(150), default="Data Engineer / Developer")
    domain = Column(String(100), default="Healthcare / Data Engineering")
    description = Column(Text, nullable=False)
    technologies = Column(JSON, default=list)  # ["Python", "PySpark", "Snowflake", "dbt"]
    repo_url = Column(String(255), nullable=True)
    live_url = Column(String(255), nullable=True)
    highlights = Column(JSON, default=list)  # Bullet points of key impact

    # Relationships
    profile = relationship("CandidateProfile", back_populates="projects")


class CandidateResume(Base):
    __tablename__ = "candidate_resumes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    file_type = Column(String(50), default="application/pdf")  # pdf, docx
    parsed_raw_text = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship("CandidateProfile", back_populates="resumes")

