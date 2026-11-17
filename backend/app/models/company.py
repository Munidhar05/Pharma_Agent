from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    industry_category = Column(String(100), index=True, nullable=False)  
    # "Indian Pharma", "Global Pharma", "CRO & Clinical Research", "Biotech & Life Sciences", "Pharma Tech"
    
    website = Column(String(255), nullable=True)
    careers_url = Column(String(500), nullable=True)
    hq_location = Column(String(150), default="India")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    career_sources = relationship("CompanyCareerSource", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("DiscoveredJob", back_populates="company", cascade="all, delete-orphan")


class CompanyCareerSource(Base):
    __tablename__ = "company_career_sources"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)  # Workday, Greenhouse, Lever, Taleo, SuccessFactors, Direct, RSS
    base_url = Column(String(500), nullable=False)
    career_url = Column(String(500), nullable=False)
    api_endpoint = Column(String(500), nullable=True)
    scrape_config = Column(JSON, default=dict)  # Rate limits, search terms, JSON paths
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="career_sources")


class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)  # "Official ATS", "LinkedIn Jobs", "Naukri", "Indeed"
    source_type = Column(String(50), nullable=False)  # "direct_ats", "portal_api", "rss_feed", "public_search"
    base_url = Column(String(500), nullable=False)
    rate_limit_per_min = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    last_crawled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    discovered_jobs = relationship("DiscoveredJob", back_populates="source")

