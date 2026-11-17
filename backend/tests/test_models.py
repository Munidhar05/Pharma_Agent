import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
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
    AgentExecutionLog
)


def test_user_and_preferences(test_db):
    user = User(
        email="test@pharma.com",
        password_hash="secret_hash",
        full_name="Dr. Reddy Scientist",
        role="candidate"
    )
    test_db.add(user)
    test_db.commit()

    assert user.id is not None
    assert user.role == "candidate"

    prefs = UserPreferences(
        user_id=user.id,
        preferred_locations=["Hyderabad", "Bengaluru"],
        preferred_domains=["Data Engineering", "Clinical Data"],
        min_match_score_alert=75
    )
    test_db.add(prefs)
    test_db.commit()

    assert user.preferences is not None
    assert "Hyderabad" in user.preferences.preferred_locations


def test_candidate_profile_and_relations(test_db):
    user = User(
        email="fresher.data@pharma.com",
        password_hash="secret_hash",
        full_name="Data Aspirant",
        role="candidate"
    )
    test_db.add(user)
    test_db.commit()

    profile = CandidateProfile(
        user_id=user.id,
        headline="Junior Data Engineer | Snowflake & PySpark",
        total_experience_years=0.5,
        current_location="Hyderabad",
        willing_to_relocate=True,
        verified_by_candidate=True
    )
    test_db.add(profile)
    test_db.commit()

    # Add Skills
    skill1 = CandidateSkill(profile_id=profile.id, name="Python", category="Programming", years_experience=1.5)
    skill2 = CandidateSkill(profile_id=profile.id, name="Snowflake", category="Database", years_experience=1.0)
    test_db.add_all([skill1, skill2])

    # Add Education
    edu = CandidateEducation(
        profile_id=profile.id,
        degree="B.Tech",
        field_of_study="Computer Science",
        institution="JNTU Hyderabad",
        cgpa_or_percentage=8.5,
        is_highest=True
    )
    test_db.add(edu)

    # Add Project
    proj = CandidateProject(
        profile_id=profile.id,
        title="Pharma Medallion Lakehouse",
        role="Data Engineer",
        domain="Life Sciences",
        description="Built Databricks Delta Lake pipeline",
        technologies=["Python", "PySpark", "Databricks"]
    )
    test_db.add(proj)
    test_db.commit()

    assert len(profile.skills) == 2
    assert len(profile.education) == 1
    assert len(profile.projects) == 1
    assert profile.projects[0].technologies == ["Python", "PySpark", "Databricks"]


def test_company_and_job_deduplication(test_db):
    company = Company(
        name="Novartis India",
        slug="novartis-india",
        industry_category="Global Pharma",
        hq_location="Hyderabad",
        careers_url="https://novartis.com/careers"
    )
    test_db.add(company)
    test_db.commit()

    job_source = JobSource(
        name="Official Workday",
        source_type="direct_ats",
        base_url="https://novartis.wd3.myworkdayjobs.com"
    )
    test_db.add(job_source)
    test_db.commit()

    job = DiscoveredJob(
        job_uid="novartis_req_101_hyd",
        company_id=company.id,
        source_id=job_source.id,
        title="Associate Data Engineer",
        req_id="REQ-101",
        category="Data Engineering",
        city="Hyderabad",
        work_mode="Hybrid",
        min_experience=0.0,
        max_experience=2.0,
        description="Looking for an Associate Data Engineer with Python and SQL skills in clinical analytics.",
        official_application_url="https://novartis.com/careers/req101",
        canonical_url="https://novartis.com/careers/req101",
        status="ACTIVE"
    )
    test_db.add(job)
    test_db.commit()

    assert job.id is not None
    assert job.company.name == "Novartis India"
    assert job.source.name == "Official Workday"

    # Verify duplicate job_uid fails due to unique constraint
    duplicate_job = DiscoveredJob(
        job_uid="novartis_req_101_hyd",  # Same UID
        company_id=company.id,
        title="Associate Data Engineer - Duplicate",
        description="Duplicate posting",
        official_application_url="https://novartis.com/careers/req101",
        canonical_url="https://novartis.com/careers/req101"
    )
    test_db.add(duplicate_job)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_matching_and_application_lifecycle(test_db):
    # Setup Company & Job
    comp = Company(name="Cipla Limited", slug="cipla", industry_category="Indian Pharma")
    test_db.add(comp)
    test_db.commit()

    job = DiscoveredJob(
        job_uid="cipla_job_202",
        company_id=comp.id,
        title="Junior Clinical Data Analyst",
        category="Clinical Data",
        city="Mumbai",
        description="Analyze clinical trials data with SQL and Python",
        official_application_url="https://cipla.com/careers/202",
        canonical_url="https://cipla.com/careers/202",
        status="ACTIVE"
    )
    test_db.add(job)

    # Setup User & Candidate
    user = User(email="applicant@pharma.com", password_hash="hash", full_name="Pharma Applicant")
    test_db.add(user)
    test_db.commit()

    candidate = CandidateProfile(user_id=user.id, headline="Data Analyst")
    test_db.add(candidate)
    test_db.commit()

    # 1. Job Match Result
    match = JobMatchResult(
        job_id=job.id,
        profile_id=candidate.id,
        overall_score=85.5,
        skills_score=88.0,
        experience_score=90.0,
        education_score=95.0,
        responsibility_score=80.0,
        industry_score=75.0,
        location_score=85.0,
        eligibility_label="Strong match",
        is_hard_eligible=True,
        matched_skills=["Python", "SQL"],
        missing_skills=["SAS"]
    )
    test_db.add(match)
    test_db.commit()

    assert match.eligibility_label == "Strong match"
    assert match.overall_score == 85.5

    # 2. Generated Tailored Resume
    tailored_resume = GeneratedResume(
        profile_id=candidate.id,
        job_id=job.id,
        title="Cipla Clinical Data Analyst ATS Resume",
        keyword_coverage_score=88.0,
        file_path_pdf="/path/to/resume.pdf",
        file_path_docx="/path/to/resume.docx"
    )
    test_db.add(tailored_resume)
    test_db.commit()

    # 3. Application Record & Event Audit Trail
    app = ApplicationRecord(
        candidate_id=candidate.id,
        job_id=job.id,
        resume_id=tailored_resume.id,
        mode="Assisted application with approval",
        status="Awaiting approval",
        candidate_approved=False
    )
    test_db.add(app)
    test_db.commit()

    assert app.id is not None
    assert app.status == "Awaiting approval"

    # Simulate Candidate Approval and Submission
    app.candidate_approved = True
    app.approved_at = datetime.utcnow()
    app.status = "Submitted"
    app.submission_ref_id = "CIPLA-2026-APP-998"

    event = ApplicationEvent(
        application_id=app.id,
        previous_status="Awaiting approval",
        new_status="Submitted",
        event_source="Candidate",
        notes="Candidate verified form preview and clicked Approve & Submit."
    )
    test_db.add(event)
    test_db.commit()

    assert len(app.events) == 1
    assert app.events[0].new_status == "Submitted"
    assert app.submission_ref_id == "CIPLA-2026-APP-998"


def test_agent_execution_logs_and_notifications(test_db):
    user = User(email="notify@pharma.com", password_hash="hash", full_name="Notifier")
    test_db.add(user)
    test_db.commit()

    notif = Notification(
        user_id=user.id,
        title="High Match Found: BMS Junior Data Engineer",
        message="Match score 91% for Bristol Myers Squibb Hyderabad opening.",
        notification_type="JobMatch"
    )
    test_db.add(notif)

    log = AgentExecutionLog(
        agent_name="JobSearchAgent",
        execution_id="exec_cycle_101",
        task_type="Discovery",
        status="SUCCESS",
        items_processed=42,
        items_failed=0
    )
    test_db.add(log)
    test_db.commit()

    assert notif.id is not None
    assert notif.is_read is False
    assert log.items_processed == 42

