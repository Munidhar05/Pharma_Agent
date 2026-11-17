import pytest
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import (
    User,
    UserPreferences,
    CandidateProfile,
    CandidateSkill,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    Company,
    CompanyCareerSource,
    JobSource,
    DiscoveredJob,
    JobRequirement,
    JobSkill,
    JobMatchResult,
    GeneratedResume,
    ApplicationRecord,
    ApplicationEvent,
    Notification,
    AgentExecutionLog,
    SearchHistory
)

# Test in-memory database
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

