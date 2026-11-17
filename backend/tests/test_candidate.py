import os
import pytest
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import docx
from fastapi import UploadFile

from backend.app.services.resume_parser import ResumeParserService
from backend.app.agents.candidate_profile import CandidateProfileAgent
from backend.app.models import CandidateProfile, CandidateSkill, CandidateEducation, CandidateProject, User
from backend.app.schemas.candidate import (
    CandidateProfileUpdate,
    CandidateSkillCreate,
    CandidateProjectCreate
)
from backend.app.api.v1.candidate import (
    get_profile,
    update_profile,
    verify_candidate_profile,
    add_skill,
    delete_skill,
    add_project,
    delete_project,
    upload_resume,
    list_resumes,
    get_current_candidate_profile
)


def create_synthetic_pdf(file_path: str) -> None:
    """Helper to generate a realistic synthetic PDF resume for testing."""
    c = canvas.Canvas(file_path, pagesize=letter)
    c.drawString(100, 750, "Munidhar Kandula - Data Engineer")
    c.drawString(100, 730, "Email: munidhar.kandula@example.com | Phone: +919876543210")
    c.drawString(100, 715, "LinkedIn: https://linkedin.com/in/munidhar-kandula | GitHub: https://github.com/munidhar-k")
    c.drawString(100, 690, "Summary: Junior Data Engineer with 1 year experience in PySpark, Snowflake, Databricks, and dbt.")
    c.drawString(100, 670, "Education: B.Tech in Computer Science and Engineering, 2024, CGPA: 8.4")
    c.drawString(100, 650, "Technical Skills: Python, SQL, Snowflake, Databricks, PySpark, dbt, Power BI, ETL, LIMS, GxP, CSV")
    c.drawString(100, 630, "Project: Medallion Architecture Data Pipeline with Delta Lake on Databricks")
    c.drawString(100, 610, "Project: Automated Data Quality Validation on Snowflake with Great Expectations")
    c.save()


def create_synthetic_docx(file_path: str) -> None:
    """Helper to generate a realistic synthetic DOCX resume for testing."""
    doc = docx.Document()
    doc.add_heading("Candidate Test Resume", 0)
    doc.add_paragraph("Email: candidate.docx@example.com | Phone: 9876543211")
    doc.add_paragraph("LinkedIn: https://linkedin.com/in/candidate-docx")
    doc.add_paragraph("Education: Master of Science (M.Sc) in Bioinformatics, 2023, Percentage: 82")
    doc.add_paragraph("Skills: Python, SQL, Clinical Data Management, Pharmacovigilance, SDTM, AWS, Tableau")
    doc.add_paragraph("Experience: 0.5 years of experience as Clinical Data Analyst Intern.")
    doc.save(file_path)


def test_resume_parser_service_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        create_synthetic_pdf(tmp_path)
        parsed = ResumeParserService.parse_resume(tmp_path)

        assert parsed["email"] == "munidhar.kandula@example.com"
        assert parsed["phone"] is not None and "9876543210" in parsed["phone"]
        assert "linkedin.com/in/munidhar-kandula" in parsed["linkedin_url"]
        assert "github.com/munidhar-k" in parsed["github_url"]

        skill_names = [s["name"] for s in parsed["skills"]]
        assert "Python" in skill_names
        assert "SQL" in skill_names
        assert "Snowflake" in skill_names
        assert "Databricks" in skill_names
        assert "PySpark" in skill_names
        assert "dbt" in skill_names
        assert "LIMS" in skill_names
        assert "GxP" in skill_names

        assert len(parsed["projects"]) >= 2
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_resume_parser_service_docx():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        create_synthetic_docx(tmp_path)
        parsed = ResumeParserService.parse_resume(tmp_path)

        assert parsed["email"] == "candidate.docx@example.com"
        skill_names = [s["name"] for s in parsed["skills"]]
        assert "Python" in skill_names
        assert "Clinical Data Management" in skill_names
        assert "Pharmacovigilance" in skill_names
        assert "Tableau" in skill_names
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_candidate_profile_agent(test_db):
    user = User(email="agent_test@pharma.com", password_hash="hash", full_name="Agent Tester")
    test_db.add(user)
    test_db.commit()

    profile = CandidateProfile(
        user_id=user.id,
        phone="+91-9988776655",
        linkedin_url="https://linkedin.com/in/tester",
        github_url="https://github.com/tester",
        verified_by_candidate=False
    )
    test_db.add(profile)
    test_db.commit()

    # Add skills
    for name in ["Python", "SQL", "Snowflake", "Databricks", "dbt"]:
        test_db.add(CandidateSkill(profile_id=profile.id, name=name))

    # Add Education
    test_db.add(CandidateEducation(profile_id=profile.id, degree="B.Tech", field_of_study="CSE", institution="JNTU"))

    # Add Project
    test_db.add(CandidateProject(
        profile_id=profile.id,
        title="Medallion Pipeline",
        description="Databricks pipeline",
        technologies=["Python", "PySpark"]
    ))
    test_db.commit()

    agent = CandidateProfileAgent(profile)
    analysis = agent.analyze_profile()

    assert analysis["completeness_score"] > 60
    assert "Explicit candidate verification" in analysis["missing_items"]
    assert "Python" in analysis["pharma_relevant_skills"]

    # Verify
    profile.verified_by_candidate = True
    test_db.commit()
    updated_analysis = agent.analyze_profile()
    assert updated_analysis["is_verified"] is True
    assert updated_analysis["status"] == "Ready for Discovery"


def test_candidate_api_route_functions(test_db):
    # Setup test user and profile
    user = User(email="api_test@pharma.com", password_hash="hash", full_name="API Tester", role="candidate")
    test_db.add(user)
    test_db.commit()

    profile = CandidateProfile(
        user_id=user.id,
        headline="Initial Headline",
        current_location="Hyderabad",
        total_experience_years=0.5,
        verified_by_candidate=False
    )
    test_db.add(profile)
    test_db.commit()

    # 1. Get profile
    res = get_profile(db=test_db, profile=profile)
    assert res.full_name == "API Tester"
    assert res.verified_by_candidate is False

    # 2. Update profile
    update_data = CandidateProfileUpdate(
        headline="Updated Lead Data Engineer",
        current_location="Bengaluru",
        total_experience_years=1.0,
        expected_ctc=800000.0
    )
    updated = update_profile(payload=update_data, db=test_db, profile=profile)
    assert updated.headline == "Updated Lead Data Engineer"
    assert updated.current_location == "Bengaluru"
    assert updated.expected_ctc == 800000.0

    # 3. Add skill
    new_skill = CandidateSkillCreate(
        name="Apache Kafka",
        category="Data Engineering",
        proficiency="Intermediate",
        years_experience=1.0,
        verified=True
    )
    skill_rec = add_skill(skill_in=new_skill, db=test_db, profile=profile)
    assert skill_rec.name == "Apache Kafka"

    # 4. Add project
    new_proj = CandidateProjectCreate(
        title="Clinical Trials Ingestion",
        role="Data Engineer",
        domain="Clinical Research",
        description="Streamed patient vitals data via Kafka to Databricks.",
        technologies=["Kafka", "Python", "Databricks"],
        highlights=["Zero message loss under 10k eps"]
    )
    proj_rec = add_project(project_in=new_proj, db=test_db, profile=profile)
    assert proj_rec.title == "Clinical Trials Ingestion"

    # 5. Verify candidate profile
    verify_res = verify_candidate_profile(db=test_db, profile=profile)
    assert verify_res["verified_by_candidate"] is True
    assert profile.verified_by_candidate is True

    # 6. Delete skill & project
    del_skill_res = delete_skill(skill_id=skill_rec.id, db=test_db, profile=profile)
    assert del_skill_res["status"] == "success"

    del_proj_res = delete_project(project_id=proj_rec.id, db=test_db, profile=profile)
    assert del_proj_res["status"] == "success"


def test_upload_resume_route_function(test_db):
    user = User(email="upload_test@pharma.com", password_hash="hash", full_name="Upload Tester", role="candidate")
    test_db.add(user)
    test_db.commit()

    profile = CandidateProfile(user_id=user.id, headline="Aspirant")
    test_db.add(profile)
    test_db.commit()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        create_synthetic_pdf(tmp_path)
        with open(tmp_path, "rb") as f:
            upload_file = UploadFile(file=f, filename="synthetic_resume.pdf")
            upload_res = upload_resume(file=upload_file, db=test_db, profile=profile)

        assert upload_res.filename == "synthetic_resume.pdf"
        assert upload_res.extracted_data_summary["skills_found"] > 0
        assert upload_res.verification_required is True

        resumes = list_resumes(profile=profile)
        assert len(resumes) >= 1
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
