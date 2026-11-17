import os
import tempfile
import pytest
from datetime import datetime
import docx

from backend.app.services.resume_builder import ResumeBuilderService
from backend.app.agents.ats_optimization import ATSOptimizationAgent
from backend.app.agents.resume_generation import ResumeGenerationAgent
from backend.app.models import (
    User,
    CandidateProfile,
    CandidateSkill,
    CandidateEducation,
    CandidateProject,
    Company,
    DiscoveredJob,
    GeneratedResume,
    AgentExecutionLog
)
from backend.app.api.v1.resumes import (
    generate_resume_for_job,
    get_resume_by_job,
    get_resume_detail,
    get_resume_keyword_coverage,
    download_resume_pdf,
    download_resume_docx,
    approve_generated_resume,
    list_all_generated_resumes
)


def create_candidate_and_job(db):
    user = User(email="ats.candidate@pharma.com", password_hash="hash", full_name="Ats Candidate", role="candidate")
    db.add(user)
    db.commit()

    profile = CandidateProfile(
        user_id=user.id,
        headline="Junior Data Engineer",
        summary="Data Engineer with Snowflake, Databricks, PySpark, and dbt expertise.",
        phone="+916303362149",
        current_location="Hyderabad",
        willing_to_relocate=True,
        verified_by_candidate=True
    )
    db.add(profile)
    db.commit()

    # Verified Skills
    for s_name in ["Python", "SQL", "Snowflake", "Databricks", "PySpark", "dbt", "LIMS"]:
        db.add(CandidateSkill(profile_id=profile.id, name=s_name, proficiency="Intermediate"))

    # Education
    db.add(CandidateEducation(
        profile_id=profile.id,
        degree="B.Tech",
        field_of_study="Computer Science and Engineering",
        institution="JNTU Hyderabad",
        end_year=2024,
        is_highest=True
    ))

    # Project
    db.add(CandidateProject(
        profile_id=profile.id,
        title="Medallion Lakehouse Architecture",
        role="Lead Pipeline Developer",
        description="Engineered Delta Lake batch and streaming pipelines on Databricks.",
        technologies=["Python", "PySpark", "Databricks", "Delta Lake", "SQL"],
        highlights=["Reduced query latency by 40%"]
    ))
    db.commit()

    comp = Company(name="AstraZeneca India", slug="astrazeneca-india", industry_category="Global Pharma")
    db.add(comp)
    db.commit()

    job = DiscoveredJob(
        job_uid="az_ats_test_01",
        company_id=comp.id,
        title="Associate Data Engineer",
        category="Data Engineering",
        city="Bengaluru",
        min_experience=0.0,
        max_experience=2.0,
        description="Requires Python, SQL, Databricks, PySpark, Snowflake, and AWS Glue.",
        official_application_url="https://test.internal/job/az-01",
        canonical_url="https://test.internal/job/az-01",
        status="ACTIVE"
    )
    test_db_job = db.add(job)
    db.commit()
    db.refresh(profile)
    db.refresh(job)

    return profile, job


def test_resume_builder_service_pdf_and_docx():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_file = os.path.join(tmpdir, "test_resume.pdf")
        docx_file = os.path.join(tmpdir, "test_resume.docx")

        contact = {"email": "test@pharma.com", "phone": "+91-9999999999", "location": "Hyderabad"}
        skills = ["Python", "SQL", "Snowflake", "Databricks", "PySpark"]
        education = [{"degree": "B.Tech", "field_of_study": "CSE", "institution": "JNTU", "end_year": 2024}]
        projects = [{
            "title": "Clinical Lakehouse",
            "role": "Data Engineer",
            "technologies": ["Python", "Databricks"],
            "description": "Constructed clinical data pipeline",
            "highlights": ["Zero record loss"]
        }]

        # 1. Test PDF generation
        ResumeBuilderService.generate_pdf_resume(
            output_path=pdf_file,
            full_name="Dr. Candidate",
            contact_info=contact,
            headline="Lead Data Engineer",
            summary="Experienced professional",
            skills=skills,
            education=education,
            projects=projects
        )
        assert os.path.exists(pdf_file)
        assert os.path.getsize(pdf_file) > 1000

        with open(pdf_file, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"

        # 2. Test DOCX generation
        ResumeBuilderService.generate_docx_resume(
            output_path=docx_file,
            full_name="Dr. Candidate",
            contact_info=contact,
            headline="Lead Data Engineer",
            summary="Experienced professional",
            skills=skills,
            education=education,
            projects=projects
        )
        assert os.path.exists(docx_file)
        assert os.path.getsize(docx_file) > 1000

        # Validate reopening with docx library
        doc = docx.Document(docx_file)
        assert any("Dr. Candidate" in p.text for p in doc.paragraphs)
        assert any("TECHNICAL SKILLS" in p.text for p in doc.paragraphs)


def test_ats_optimization_agent(test_db):
    candidate, job = create_candidate_and_job(test_db)
    agent = ATSOptimizationAgent(candidate=candidate, job=job)

    # Coverage Report
    report = agent.generate_coverage_report()
    assert report.total_keywords_found >= 4
    assert report.matched_count >= 3
    assert report.coverage_percentage > 60.0

    matched_keywords = [item.keyword for item in report.items if item.status == "Matched"]
    assert "Python" in matched_keywords
    assert "Databricks" in matched_keywords
    assert "PySpark" in matched_keywords

    # Optimized Content
    content = agent.optimize_resume_content()
    assert "Python" in content.selected_skills[:3]
    assert len(content.selected_projects) >= 1
    assert "AstraZeneca" in content.summary


def test_resume_generation_agent_and_api(test_db):
    candidate, job = create_candidate_and_job(test_db)

    # 1. Generate via Agent
    agent = ResumeGenerationAgent(db=test_db)
    rec = agent.generate_tailored_resume(candidate=candidate, job=job)

    assert rec.id is not None
    assert rec.profile_id == candidate.id
    assert rec.job_id == job.id
    assert rec.keyword_coverage_score > 60.0
    assert os.path.exists(rec.file_path_pdf)
    assert os.path.exists(rec.file_path_docx)

    # Verify AgentExecutionLog
    log = test_db.query(AgentExecutionLog).filter(
        AgentExecutionLog.agent_name == "ResumeGenerationAgent"
    ).first()
    assert log is not None
    assert log.status == "SUCCESS"

    # 2. Get via API
    resp = get_resume_by_job(job_id=job.id, db=test_db, profile=candidate)
    assert resp.id == rec.id
    assert resp.pdf_download_url is not None

    # 3. Get Detail via API
    detail_resp = get_resume_detail(resume_id=rec.id, db=test_db, profile=candidate)
    assert detail_resp.id == rec.id

    # 4. Coverage Report via API
    cov_resp = get_resume_keyword_coverage(resume_id=rec.id, db=test_db, profile=candidate)
    assert cov_resp.matched_count >= 3

    # 5. Approve via API
    assert rec.is_approved_by_user is False
    approved_resp = approve_generated_resume(resume_id=rec.id, db=test_db, profile=candidate)
    assert approved_resp.is_approved_by_user is True

    # 6. Test Downloads via API
    pdf_resp = download_resume_pdf(resume_id=rec.id, db=test_db, profile=candidate)
    assert pdf_resp.media_type == "application/pdf"

    docx_resp = download_resume_docx(resume_id=rec.id, db=test_db, profile=candidate)
    assert "wordprocessingml" in docx_resp.media_type

    # 7. List All Resumes
    all_resumes = list_all_generated_resumes(db=test_db, profile=candidate)
    assert len(all_resumes) >= 1

