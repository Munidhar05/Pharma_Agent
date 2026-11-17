import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models.user import User, UserPreferences
from backend.app.models.candidate import (
    CandidateProfile, CandidateSkill, CandidateEducation, CandidateProject
)
from backend.app.models.company import Company
from backend.app.models.job import DiscoveredJob
from backend.app.models.resume import GeneratedResume
from backend.app.models.application import ApplicationRecord, ApplicationEvent
from backend.app.models.audit import Notification
from backend.app.services.form_mapper import FormMapperService
from backend.app.agents.application_automation import ApplicationAutomationAgent
from backend.app.agents.application_tracking import ApplicationTrackingAgent
from backend.app.schemas.application import (
    ApplicationRecordCreate,
    ApplicationApprovalRequest,
    ApplicationStatusUpdateRequest
)
from backend.app.api.v1.applications import (
    prepare_application,
    get_application_preview,
    approve_application,
    submit_application,
    update_application_status,
    list_applications,
    get_application_statistics,
    get_application_events
)


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed User
    user = User(
        email="candidate.pharma@feuji.com",
        password_hash="argon2_hashed_secret",
        full_name="Rajesh Sharma",
        role="candidate"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Seed Profile
    profile = CandidateProfile(
        user_id=user.id,
        headline="Associate Data Engineer | PySpark & Snowflake",
        summary="Data Engineer with expertise in PySpark, Databricks, Snowflake, and dbt.",
        phone="+91-9876543210",
        linkedin_url="https://linkedin.com/in/rajesh-sharma-data",
        github_url="https://github.com/rajesh-data-eng",
        total_experience_years=0.5,
        current_location="Hyderabad",
        willing_to_relocate=True,
        expected_ctc=650000.0,
        current_ctc=350000.0,
        notice_period_days=0,
        verified_by_candidate=True
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Seed Skills
    skills = [
        CandidateSkill(profile_id=profile.id, name="Python", category="Programming", years_experience=1.0),
        CandidateSkill(profile_id=profile.id, name="SQL", category="Database", years_experience=1.0),
        CandidateSkill(profile_id=profile.id, name="PySpark", category="Big Data", years_experience=0.8),
        CandidateSkill(profile_id=profile.id, name="Databricks", category="Cloud/Platform", years_experience=0.8),
        CandidateSkill(profile_id=profile.id, name="Snowflake", category="Database", years_experience=0.6),
        CandidateSkill(profile_id=profile.id, name="dbt", category="ETL", years_experience=0.5),
    ]
    db.add_all(skills)

    # Seed Education
    edu = CandidateEducation(
        profile_id=profile.id,
        degree="B.Tech",
        field_of_study="Computer Science and Engineering",
        institution="JNTU Hyderabad",
        start_year=2020,
        end_year=2024,
        cgpa_or_percentage=8.5,
        is_highest=True
    )
    db.add(edu)

    # Seed Project
    project = CandidateProject(
        profile_id=profile.id,
        title="Pharma & Healthcare Data Lakehouse",
        role="Data Engineer",
        domain="Healthcare Data Engineering",
        description="Built automated ETL pipeline using PySpark and Databricks with Medallion architecture.",
        technologies=["Python", "PySpark", "Snowflake", "Databricks"]
    )
    db.add(project)

    # Seed Company
    company = Company(
        name="Dr. Reddy's Laboratories",
        slug="dr-reddys-laboratories",
        industry_category="Indian Pharma",
        hq_location="Hyderabad, Telangana",
        website="https://www.drreddys.com",
        careers_url="https://careers.drreddys.com"
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # Seed DiscoveredJob
    job = DiscoveredJob(
        job_uid="hash_dr_reddys_data_eng_001",
        company_id=company.id,
        title="Associate Data Engineer - Clinical Data Platforms",
        category="Data Engineering",
        location="Hyderabad, Telangana",
        city="Hyderabad",
        work_mode="Hybrid",
        employment_type="Full-time",
        min_experience=0.0,
        max_experience=2.0,
        education_requirements="B.Tech in CSE / IT or related field",
        description="Looking for an Associate Data Engineer to build data ingestion pipelines using Python, SQL, PySpark, and Snowflake.",
        official_application_url="https://careers.drreddys.com/jobs/102938",
        canonical_url="https://careers.drreddys.com/jobs/102938",
        status="ACTIVE"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Seed GeneratedResume
    resume = GeneratedResume(
        profile_id=profile.id,
        job_id=job.id,
        title="ATS Tailored Resume - Dr. Reddy's",
        file_path_pdf="data/resumes/generated/test_resume.pdf",
        file_path_docx="data/resumes/generated/test_resume.docx",
        keyword_coverage_score=85.0
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    try:
        yield db
    finally:
        db.close()


def test_form_mapper_service_fields_and_screening(test_db):
    """Test FormMapperService maps standard fields and answers screening questions truthfully."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()
    resume = test_db.query(GeneratedResume).first()

    fields = FormMapperService.map_standard_fields(candidate, job, resume)
    assert len(fields) >= 10

    fields_dict = {f.field_name: f.field_value for f in fields}
    assert fields_dict["full_name"] == "Rajesh Sharma"
    assert fields_dict["first_name"] == "Rajesh"
    assert fields_dict["email"] == "candidate.pharma@feuji.com"
    assert fields_dict["phone"] == "+91-9876543210"
    assert fields_dict["current_location"] == "Hyderabad"
    assert fields_dict["willing_to_relocate"] == "Yes"
    assert fields_dict["degree"] == "B.Tech"
    assert fields_dict["institution"] == "JNTU Hyderabad"
    assert "Python" in fields_dict["technical_skills"]
    assert "Snowflake" in fields_dict["technical_skills"]

    # Truthful screening questions
    screening = FormMapperService.answer_screening_questions(candidate, job)
    assert len(screening) >= 5

    screening_dict = {s.question: s for s in screening}

    # Python experience check
    python_q = [s for s in screening if "python" in s.question.lower()][0]
    assert "1.0 year(s)" in python_q.answer
    assert python_q.is_truthful is True

    # Total experience check
    exp_q = [s for s in screening if "total" in s.question.lower()][0]
    assert "0.5 year(s)" in exp_q.answer

    # Notice period check
    notice_q = [s for s in screening if "notice" in s.question.lower()][0]
    assert "Immediate" in notice_q.answer


def test_application_automation_prepare_and_preview(test_db):
    """Test ApplicationAutomationAgent prepares application and halts at approval gate."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()
    resume = test_db.query(GeneratedResume).first()

    agent = ApplicationAutomationAgent(test_db)
    preview = agent.prepare_application(
        candidate_id=candidate.id,
        job_id=job.id,
        resume_id=resume.id,
        mode="Assisted application with approval"
    )

    assert preview.application_id is not None
    assert preview.candidate_approved is False
    assert preview.can_submit is False
    assert preview.status == "Awaiting approval"
    assert preview.job_title == "Associate Data Engineer - Clinical Data Platforms"
    assert preview.company_name == "Dr. Reddy's Laboratories"
    assert len(preview.mapped_fields) > 5
    assert len(preview.blockers) > 0
    assert any("approval" in b.lower() for b in preview.blockers)

    # Verify database record
    record = test_db.query(ApplicationRecord).filter(ApplicationRecord.id == preview.application_id).first()
    assert record is not None
    assert record.status == "Awaiting approval"
    assert record.candidate_approved is False


def test_submission_strictly_enforces_candidate_approval(test_db):
    """Test that attempting to submit an unapproved application raises a strict security/compliance error."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()

    agent = ApplicationAutomationAgent(test_db)
    preview = agent.prepare_application(
        candidate_id=candidate.id,
        job_id=job.id,
        mode="Assisted application with approval"
    )

    # Attempt submission without candidate approval
    with pytest.raises(ValueError) as excinfo:
        agent.submit_application(preview.application_id)
    assert "Candidate explicit approval is required" in str(excinfo.value)


def test_approval_and_submission_workflow(test_db):
    """Test full workflow: prepare -> approve -> submit -> verified confirmation."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()

    agent = ApplicationAutomationAgent(test_db)
    preview = agent.prepare_application(
        candidate_id=candidate.id,
        job_id=job.id
    )

    # Candidate approves application
    approved_record = agent.approve_application(
        application_id=preview.application_id,
        notes="Verified all fields and ATS resume. Ready to submit."
    )
    assert approved_record.candidate_approved is True
    assert approved_record.approved_at is not None

    # Preview now shows can_submit is True
    updated_preview = agent.get_application_preview(preview.application_id)
    assert updated_preview.candidate_approved is True
    assert updated_preview.can_submit is True

    # Candidate submits application
    result = agent.submit_application(preview.application_id)
    assert result.status == "Application confirmed"
    assert result.submission_ref_id is not None
    assert "APP-" in result.submission_ref_id
    assert result.applied_at is not None
    assert len(result.next_steps) > 0

    # Verify event trail
    events = (
        test_db.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == preview.application_id)
        .all()
    )
    assert len(events) >= 3  # Prepared, Approved, Submitted/Confirmed


def test_duplicate_application_prevention(test_db):
    """Test duplicate check prevents creating multiple application records for the same job."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()

    agent = ApplicationAutomationAgent(test_db)

    # First preparation
    preview1 = agent.prepare_application(candidate_id=candidate.id, job_id=job.id)

    # Second preparation attempt
    preview2 = agent.prepare_application(candidate_id=candidate.id, job_id=job.id)

    # Must return the same application ID
    assert preview1.application_id == preview2.application_id

    # Check database count is exactly 1
    total_apps = (
        test_db.query(ApplicationRecord)
        .filter(
            ApplicationRecord.candidate_id == candidate.id,
            ApplicationRecord.job_id == job.id
        )
        .count()
    )
    assert total_apps == 1


def test_application_tracking_lifecycle_and_milestones(test_db):
    """Test ApplicationTrackingAgent transitions statuses, creates notifications, and computes statistics."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()

    tracking_agent = ApplicationTrackingAgent(test_db)

    app = ApplicationRecord(
        candidate_id=candidate.id,
        job_id=job.id,
        status="Submitted",
        candidate_approved=True,
        applied_at=datetime.utcnow()
    )
    test_db.add(app)
    test_db.commit()
    test_db.refresh(app)

    # Transition to Interview scheduled
    updated = tracking_agent.transition_status(
        application_id=app.id,
        new_status="Interview scheduled",
        event_source="External_Webhook",
        notes="HR scheduled Technical Interview via Teams."
    )
    assert updated.status == "Interview scheduled"

    # Notification must be logged
    notif = (
        test_db.query(Notification)
        .filter(Notification.user_id == candidate.user_id)
        .order_by(Notification.id.desc())
        .first()
    )
    assert notif is not None
    assert "Interview" in notif.title

    # Stats calculation
    stats = tracking_agent.get_application_stats(candidate.id)
    assert stats.total_applications >= 1
    assert stats.interviews >= 1


def test_applications_api_route_functions(test_db):
    """Directly test FastAPI route handler functions for applications."""
    candidate = test_db.query(CandidateProfile).first()
    job = test_db.query(DiscoveredJob).first()

    # 1. Prepare
    create_req = ApplicationRecordCreate(
        candidate_id=candidate.id,
        job_id=job.id
    )
    preview = prepare_application(request=create_req, db=test_db)
    assert preview.application_id is not None

    app_id = preview.application_id

    # 2. Get preview
    fetched_preview = get_application_preview(id=app_id, db=test_db)
    assert fetched_preview.application_id == app_id

    # 3. Approve
    approval_req = ApplicationApprovalRequest(
        candidate_approved=True,
        notes="Approved via API test."
    )
    approved_resp = approve_application(id=app_id, approval=approval_req, db=test_db)
    assert approved_resp.candidate_approved is True

    # 4. Submit
    submit_result = submit_application(id=app_id, db=test_db)
    assert submit_result.status == "Application confirmed"

    # 5. Update Status
    status_req = ApplicationStatusUpdateRequest(
        new_status="Assessment pending",
        notes="Received HackerRank test link."
    )
    status_resp = update_application_status(id=app_id, update_req=status_req, db=test_db)
    assert status_resp.status == "Assessment pending"

    # 6. List
    app_list = list_applications(candidate_id=candidate.id, db=test_db)
    assert len(app_list) >= 1
    assert app_list[0].id == app_id

    # 7. Stats
    stats = get_application_statistics(candidate_id=candidate.id, db=test_db)
    assert stats.total_applications >= 1
    assert stats.assessments >= 1

    # 8. Events
    events = get_application_events(id=app_id, db=test_db)
    assert len(events) >= 3
