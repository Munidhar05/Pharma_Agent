import pytest
from datetime import datetime

from backend.app.services.scoring_engine import ScoringEngineService
from backend.app.agents.job_matching import JobMatchingAgent
from backend.app.models import (
    User,
    UserPreferences,
    CandidateProfile,
    CandidateSkill,
    CandidateEducation,
    CandidateProject,
    Company,
    DiscoveredJob,
    JobSkill,
    JobRequirement,
    JobMatchResult,
    Notification
)
from backend.app.schemas.matching import BatchMatchRequest
from backend.app.api.v1.matching import (
    get_job_matches,
    get_single_job_match,
    evaluate_job_match,
    evaluate_all_jobs,
    get_top_recommendations
)


def create_test_candidate(db) -> CandidateProfile:
    user = User(email="matcher.candidate@pharma.com", password_hash="hash", full_name="Match Candidate", role="candidate")
    db.add(user)
    db.commit()

    profile = CandidateProfile(
        user_id=user.id,
        headline="Junior Data Engineer | Snowflake, Databricks, PySpark",
        summary="Aspirant with data engineering and clinical pipeline expertise.",
        total_experience_years=0.5,
        current_location="Hyderabad",
        willing_to_relocate=True,
        verified_by_candidate=True
    )
    db.add(profile)
    db.commit()

    # Skills: Python, SQL, Snowflake, Databricks, PySpark, dbt
    for s_name in ["Python", "SQL", "Snowflake", "Databricks", "PySpark", "dbt"]:
        db.add(CandidateSkill(profile_id=profile.id, name=s_name, proficiency="Intermediate"))

    # Education: B.Tech CSE
    db.add(CandidateEducation(
        profile_id=profile.id,
        degree="B.Tech",
        field_of_study="Computer Science and Engineering",
        institution="JNTUH",
        is_highest=True
    ))

    # Project: Medallion Lakehouse
    db.add(CandidateProject(
        profile_id=profile.id,
        title="Medallion Data Lakehouse",
        description="Built Databricks delta lake pipeline",
        technologies=["Python", "PySpark", "Databricks", "Snowflake"]
    ))

    db.commit()
    db.refresh(profile)
    return profile


def test_scoring_engine_semantic_and_breakdown(test_db):
    candidate = create_test_candidate(test_db)
    comp = Company(name="Roche India", slug="roche", industry_category="Global Pharma")
    test_db.add(comp)
    test_db.commit()

    # Job: Requires Python, SQL, Snowflake, Spark, AWS
    job = DiscoveredJob(
        job_uid="roche_test_match_01",
        company_id=comp.id,
        title="Associate Data Engineer",
        category="Data Engineering",
        city="Hyderabad",
        work_mode="Hybrid",
        min_experience=0.0,
        max_experience=2.0,
        description="Looking for Associate Data Engineer with Python, SQL, Snowflake, Spark, and AWS skills.",
        official_application_url="https://test.internal/job/roche-01",
        canonical_url="https://test.internal/job/roche-01",
        status="ACTIVE"
    )
    # Add Job skills
    job.skills.append(JobSkill(skill_name="Python", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="SQL", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="Snowflake", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="Spark", is_mandatory=True))  # Candidate has PySpark -> Partial Match
    job.skills.append(JobSkill(skill_name="AWS", is_mandatory=False))   # Missing
    test_db.add(job)
    test_db.commit()

    # Evaluate
    result = ScoringEngineService.evaluate_match(candidate=candidate, job=job)

    assert result["overall_score"] >= 80.0
    assert result["eligibility_label"] in ["Excellent match", "Strong match"]
    assert result["is_hard_eligible"] is True

    matched_names = [m["skill"] for m in result["matched_skills"]]
    assert "Python" in matched_names
    assert "SQL" in matched_names
    assert "Snowflake" in matched_names

    # Check semantic related skill match
    partial_names = [p["skill"] for p in result["partially_matched_skills"]]
    assert "Spark" in partial_names

    # Check missing skill
    missing_names = [m["skill"] for m in result["missing_skills"]]
    assert "AWS" in missing_names


def test_scoring_engine_hard_experience_mismatch(test_db):
    candidate = create_test_candidate(test_db)
    comp = Company(name="Pfizer Test", slug="pfizer-test", industry_category="Global Pharma")
    test_db.add(comp)
    test_db.commit()

    # Senior Job requiring minimum 4 years of experience
    senior_job = DiscoveredJob(
        job_uid="senior_job_uid_01",
        company_id=comp.id,
        title="Lead Principal Data Architect",
        category="Data Engineering",
        city="Mumbai",
        min_experience=4.0,
        max_experience=7.0,
        description="Requires 4+ years of experience leading pharmaceutical data lake architectures.",
        official_application_url="https://test.internal/job/senior-01",
        canonical_url="https://test.internal/job/senior-01",
        status="ACTIVE"
    )
    test_db.add(senior_job)
    test_db.commit()

    result = ScoringEngineService.evaluate_match(candidate=candidate, job=senior_job)

    assert result["is_hard_eligible"] is False
    assert any("Experience mismatch" in r for r in result["rejection_reasons"])
    assert result["eligibility_label"] == "Low match" or result["overall_score"] < 65.0


def test_job_matching_agent_and_notifications(test_db):
    candidate = create_test_candidate(test_db)
    comp = Company(name="Bristol Myers Squibb", slug="bms", industry_category="Global Pharma")
    test_db.add(comp)
    test_db.commit()

    job = DiscoveredJob(
        job_uid="bms_match_test_02",
        company_id=comp.id,
        title="Junior Data Engineer - Life Sciences",
        category="Data Engineering",
        city="Hyderabad",
        work_mode="Hybrid",
        min_experience=0.0,
        max_experience=2.0,
        description="Junior Data Engineer position in Hyderabad using Databricks, PySpark, and SQL.",
        official_application_url="https://test.internal/job/bms-02",
        canonical_url="https://test.internal/job/bms-02",
        status="ACTIVE"
    )
    job.skills.append(JobSkill(skill_name="Python", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="SQL", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="Databricks", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="PySpark", is_mandatory=True))
    test_db.add(job)
    test_db.commit()

    agent = JobMatchingAgent(db=test_db)
    
    # 1. Single evaluation
    match = agent.evaluate_candidate_for_job(candidate=candidate, job=job)
    assert match.overall_score >= 85.0
    assert match.is_hard_eligible is True
    assert match.eligibility_label in ["Excellent match", "Strong match"]

    # 2. Verify notification was dispatched
    notif = test_db.query(Notification).filter(Notification.user_id == candidate.user_id).first()
    assert notif is not None
    assert "STRONG MATCH" in notif.title

    # 3. Batch evaluation
    batch_res = agent.evaluate_all_active_jobs(candidate=candidate)
    assert batch_res["total_jobs_evaluated"] >= 1
    assert batch_res["strong_matches_count"] >= 1
    assert len(batch_res["matches"]) >= 1


def test_matching_api_route_functions(test_db):
    candidate = create_test_candidate(test_db)
    comp = Company(name="Dr. Reddy's Match", slug="dr-reddys-match", industry_category="Indian Pharma")
    test_db.add(comp)
    test_db.commit()

    job = DiscoveredJob(
        job_uid="drl_api_match_01",
        company_id=comp.id,
        title="Associate Data Engineer",
        category="Data Engineering",
        city="Hyderabad",
        min_experience=0.0,
        max_experience=2.0,
        description="Associate Data Engineer role with Python, SQL, and Snowflake.",
        official_application_url="https://test.internal/job/drl-match-01",
        canonical_url="https://test.internal/job/drl-match-01",
        status="ACTIVE"
    )
    job.skills.append(JobSkill(skill_name="Python", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="SQL", is_mandatory=True))
    job.skills.append(JobSkill(skill_name="Snowflake", is_mandatory=True))
    test_db.add(job)
    test_db.commit()

    # 1. Evaluate single job via API
    single_res = evaluate_job_match(job_id=job.id, db=test_db, profile=candidate)
    assert single_res.job_id == job.id
    assert single_res.overall_score >= 85.0

    # 2. Get single job match
    match_detail = get_single_job_match(job_id=job.id, db=test_db, profile=candidate)
    assert match_detail.job_id == job.id
    assert match_detail.score_breakdown.technical_skills_score > 0

    # 3. Batch evaluate via API
    batch_payload = BatchMatchRequest(min_score_filter=70.0)
    batch_res = evaluate_all_jobs(payload=batch_payload, db=test_db, profile=candidate)
    assert batch_res.total_jobs_evaluated >= 1
    assert batch_res.eligible_jobs_count >= 1

    # 4. List job matches with filters
    matches = get_job_matches(
        db=test_db,
        profile=candidate,
        min_score=75.0,
        hard_eligible_only=True
    )
    assert len(matches) >= 1

    # 5. Top recommendations
    top_recs = get_top_recommendations(db=test_db, profile=candidate, limit=3)
    assert len(top_recs) >= 1
    assert top_recs[0].overall_score >= 80.0

