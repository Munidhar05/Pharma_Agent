import pytest
from datetime import datetime

from backend.app.services.job_extractor import JobExtractorService
from backend.app.agents.job_extraction import JobExtractionAgent
from backend.app.agents.job_verification import JobVerificationAgent
from backend.app.agents.job_search import JobSearchAgent
from backend.app.models import Company, DiscoveredJob, JobSource, AgentExecutionLog, SearchHistory
from backend.app.schemas.job import (
    DiscoveredJobCreate,
    DiscoveredJobUpdate,
    JobSearchQuery
)
from backend.app.api.v1.jobs import (
    list_jobs,
    get_job_detail,
    create_job,
    update_job,
    trigger_job_search,
    verify_single_job,
    get_job_stats
)


def test_job_extractor_service_classification():
    # 1. Clinical Data
    cat1 = JobExtractorService.classify_category(
        title="Associate Clinical Data Programmer",
        description="Support CDISC SDTM and clinical trials data management."
    )
    assert cat1 == "Clinical and Pharmaceutical Data"

    # 2. Pharma IT & CSV
    cat2 = JobExtractorService.classify_category(
        title="CSV Validation Engineer",
        description="Execute Computer System Validation and GxP compliance protocols."
    )
    assert cat2 == "Pharma IT and Data Quality"

    # 3. Data Engineering
    cat3 = JobExtractorService.classify_category(
        title="Junior Data Engineer",
        description="Build Databricks Delta Lake and PySpark pipelines on Snowflake."
    )
    assert cat3 == "Data Engineering"

    # 4. Data Analytics
    cat4 = JobExtractorService.classify_category(
        title="Commercial Data Analyst",
        description="Develop Power BI reports and SQL queries for pharma sales."
    )
    assert cat4 == "Data Analytics"

    # 5. AI/ML
    cat5 = JobExtractorService.classify_category(
        title="Healthcare AI Engineer",
        description="Deploy machine learning and RAG systems for molecular clinical literature."
    )
    assert cat5 == "AI and Machine Learning"


def test_job_extractor_location_and_experience():
    # Location
    loc, city, mode = JobExtractorService.extract_location_and_mode("Remote India flexible role based in Hyderabad")
    assert city == "Hyderabad"
    assert mode == "Remote"

    # Experience range: Fresher
    min_e, max_e = JobExtractorService.extract_experience_range("Opportunity for Freshers / 0-2 years of experience.")
    assert min_e == 0.0
    assert max_e == 1.0

    # Experience range: Explicit bounds
    min_e2, max_e2 = JobExtractorService.extract_experience_range("Requires 1 - 3 yrs experience.")
    assert min_e2 == 1.0
    assert max_e2 == 3.0

    # Salary disclosure: Absent
    s_min, s_max, disclosed = JobExtractorService.extract_salary_details("Competitive salary based on industry standards.")
    assert disclosed is False
    assert s_min is None

    # Salary disclosure: Disclosed
    s_min2, s_max2, disclosed2 = JobExtractorService.extract_salary_details("Salary range: 6 - 9 LPA.")
    assert disclosed2 is True
    assert s_min2 == 600000.0
    assert s_max2 == 900000.0


def test_job_extraction_agent(test_db):
    comp = Company(name="Sun Pharma", slug="sun-pharma", industry_category="Indian Pharma")
    test_db.add(comp)
    test_db.commit()

    agent = JobExtractionAgent(db=test_db)
    raw = {
        "title": "Junior PySpark & Snowflake Developer",
        "req_id": "SUN-DE-01",
        "description": "Looking for Junior Data Engineer in Bengaluru with Python, SQL, Snowflake, and PySpark skills. B.Tech required.",
        "location": "Bengaluru",
        "official_url": "https://sunpharma.com/careers/sun-de-01"
    }

    job = agent.extract_and_structure_job(raw_job=raw, company=comp)
    assert job.job_uid is not None
    assert job.category == "Data Engineering"
    assert job.city == "Bengaluru"
    assert len(job.skills) >= 3

    skill_names = [s.skill_name for s in job.skills]
    assert "Python" in skill_names
    assert "SQL" in skill_names
    assert "Snowflake" in skill_names


def test_job_verification_agent(test_db):
    comp = Company(name="Cipla Test", slug="cipla-test", industry_category="Indian Pharma")
    test_db.add(comp)
    test_db.commit()

    active_job = DiscoveredJob(
        job_uid="active_uid_101",
        company_id=comp.id,
        title="Associate Analyst",
        description="Active test",
        official_application_url="https://test.internal/job/active",
        canonical_url="https://test.internal/job/active",
        status="UNKNOWN"
    )
    closed_job = DiscoveredJob(
        job_uid="closed_uid_102",
        company_id=comp.id,
        title="Associate Analyst Closed",
        description="Closed test",
        official_application_url="https://test.internal/job/closed",
        canonical_url="https://test.internal/job/closed",
        status="ACTIVE"
    )
    test_db.add_all([active_job, closed_job])
    test_db.commit()

    verifier = JobVerificationAgent(db=test_db)
    
    # 1. Verify Active
    res1 = verifier.verify_job_status(active_job)
    assert res1["current_status"] == "ACTIVE"
    assert active_job.status == "ACTIVE"

    # 2. Verify Closed
    res2 = verifier.verify_job_status(closed_job)
    assert res2["current_status"] == "CLOSED"
    assert closed_job.status == "CLOSED"


def test_job_search_agent_and_api(test_db):
    # Setup company
    comp = Company(name="Dr. Reddy's Laboratories", slug="dr-reddys", industry_category="Indian Pharma")
    test_db.add(comp)
    test_db.commit()

    # 1. Trigger search via Agent
    search_agent = JobSearchAgent(db=test_db)
    res = search_agent.execute_search(category="Data Engineering")
    assert res["new_jobs_discovered"] >= 1
    assert res["duplicates_skipped"] == 0

    # Running search again should deduplicate
    repeat_res = search_agent.execute_search(category="Data Engineering")
    assert repeat_res["new_jobs_discovered"] == 0
    assert repeat_res["duplicates_skipped"] >= 1

    # 2. List jobs via API
    jobs = list_jobs(db=test_db, category="Data Engineering")
    assert len(jobs) >= 1
    job_id = jobs[0].id

    # 3. Get job detail
    detail = get_job_detail(job_id=job_id, db=test_db)
    assert detail.id == job_id
    assert len(detail.skills) >= 1

    # 4. Update job
    update_data = DiscoveredJobUpdate(city="Hyderabad", work_mode="Remote")
    updated = update_job(job_id=job_id, payload=update_data, db=test_db)
    assert updated.city == "Hyderabad"
    assert updated.work_mode == "Remote"

    # Use internal test URL to verify active status deterministically in test environment
    updated_job_rec = test_db.query(DiscoveredJob).filter(DiscoveredJob.id == job_id).first()
    updated_job_rec.official_application_url = "https://test.internal/job/active"
    test_db.commit()

    # 5. Verify Single Job via API
    v_res = verify_single_job(job_id=job_id, db=test_db)
    assert v_res.job_id == job_id
    assert v_res.is_active is True
    assert v_res.current_status == "ACTIVE"

    # 6. Get stats summary
    stats = get_job_stats(db=test_db)
    assert stats["total_jobs_discovered"] >= 1
    assert stats["active_jobs"] >= 1
