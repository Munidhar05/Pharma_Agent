from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ApplicationRecord(Base):
    __tablename__ = "application_records"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("discovered_jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("generated_resumes.id", ondelete="SET NULL"), nullable=True)

    mode = Column(String(50), default="Assisted application with approval")
    # Status lifecycle:
    # Discovered -> Matched -> Shortlisted -> Resume generated -> Awaiting approval ->
    # Submitted -> Application confirmed -> Assessment pending -> Interview scheduled ->
    # Rejected -> Withdrawn -> Closed
    status = Column(String(50), index=True, default="Discovered")

    candidate_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)

    submission_ref_id = Column(String(100), nullable=True)  # Confirmation number from company
    submission_screenshot_path = Column(String(500), nullable=True)
    form_preview_data = Column(JSON, default=dict)          # Snapshot of mapped form fields
    screening_answers = Column(JSON, default=dict)          # Answers filled in screening questions
    
    applied_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate_profile = relationship("CandidateProfile", back_populates="applications")
    job = relationship("DiscoveredJob", back_populates="applications")
    resume = relationship("GeneratedResume", back_populates="applications")
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("application_records.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    event_source = Column(String(50), default="Agent")  # Agent, Candidate, External_Webhook, Manual
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("ApplicationRecord", back_populates="events")

