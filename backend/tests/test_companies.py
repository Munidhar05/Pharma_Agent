import pytest
from backend.app.adapters.workday_adapter import WorkdayAdapter
from backend.app.adapters.greenhouse_adapter import GreenhouseAdapter
from backend.app.adapters.lever_adapter import LeverAdapter
from backend.app.adapters import detect_career_source_type
from backend.app.services.career_discovery import CareerDiscoveryService
from backend.app.agents.company_discovery import CompanyDiscoveryAgent
from backend.app.models import Company, CompanyCareerSource, AgentExecutionLog, JobSource
from backend.app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyCareerSourceCreate,
    CompanyDiscoveryQuery
)
from backend.app.api.v1.companies import (
    list_companies,
    get_company_detail,
    create_company,
    update_company,
    add_company_career_source,
    trigger_company_discovery,
    get_company_stats,
    list_global_job_sources
)


def test_ats_adapters_detection():
    # 1. Workday
    workday_url = "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"
    assert WorkdayAdapter.can_handle(workday_url) is True
    api_endpoint = WorkdayAdapter.detect_api_endpoint(workday_url)
    assert api_endpoint == "https://pfizer.wd1.myworkdayjobs.com/wday/cxs/pfizer/PfizerCareers/jobs"

    # 2. Greenhouse
    gh_url = "https://boards.greenhouse.io/medgenome"
    assert GreenhouseAdapter.can_handle(gh_url) is True
    gh_api = GreenhouseAdapter.detect_api_endpoint(gh_url)
    assert "boards-api.greenhouse.io/v1/boards/medgenome/jobs" in gh_api

    # 3. Lever
    lever_url = "https://jobs.lever.co/saama"
    assert LeverAdapter.can_handle(lever_url) is True
    lever_api = LeverAdapter.detect_api_endpoint(lever_url)
    assert "api.lever.co/v0/postings/saama?mode=json" in lever_api

    # 4. Fallback / Direct
    direct_url = "https://careers.drreddys.com"
    source_type, endpoint = detect_career_source_type(direct_url)
    assert source_type == "Direct"
    assert endpoint is None


def test_career_discovery_service():
    # Test URL normalization
    norm = CareerDiscoveryService.normalize_url("www.cipla.com/careers/ ")
    assert norm == "https://www.cipla.com/careers"

    # Test Industry category inference
    cro_cat = CareerDiscoveryService.infer_industry_category("IQVIA Clinical Solutions")
    assert cro_cat == "CRO & Clinical Research"

    biotech_cat = CareerDiscoveryService.infer_industry_category("Syngene Biologics Genomics")
    assert biotech_cat == "Biotech & Life Sciences"

    tech_cat = CareerDiscoveryService.infer_industry_category("Veeva Life Sciences Software")
    assert tech_cat == "Pharma Tech"

    global_cat = CareerDiscoveryService.infer_industry_category("Novartis Healthcare India")
    assert global_cat == "Global Pharma"

    indian_cat = CareerDiscoveryService.infer_industry_category("Sun Pharmaceutical Industries")
    assert indian_cat == "Indian Pharma"


def test_company_discovery_agent(test_db):
    agent = CompanyDiscoveryAgent(db=test_db)
    
    # Run cycle with keyword filter
    result = agent.run_discovery_cycle(keyword="Aragen")
    assert result["items_processed"] >= 1
    assert result["new_companies_added"] == 1
    assert result["sources_detected"] >= 1

    # Check database persistence
    company = test_db.query(Company).filter(Company.name == "Aragen Life Sciences").first()
    assert company is not None
    assert company.industry_category == "CRO & Clinical Research"
    assert len(company.career_sources) == 1

    # Verify AgentExecutionLog was recorded
    log = test_db.query(AgentExecutionLog).filter(
        AgentExecutionLog.execution_id == result["execution_id"]
    ).first()
    assert log is not None
    assert log.agent_name == "CompanyDiscoveryAgent"
    assert log.status == "SUCCESS"

    # Running again should deduplicate and add 0
    repeat_res = agent.run_discovery_cycle(keyword="Aragen")
    assert repeat_res["new_companies_added"] == 0


def test_companies_api_route_functions(test_db):
    # 1. Create company via API
    payload = CompanyCreate(
        name="AmpleLogic Pharma Tech",
        slug="amplelogic-pharma-tech",
        industry_category="Pharma Tech",
        careers_url="https://jobs.lever.co/amplelogic",
        hq_location="Hyderabad",
        description="GMP compliance and data validation software"
    )
    detail = create_company(payload=payload, db=test_db)
    assert detail.name == "AmpleLogic Pharma Tech"
    assert len(detail.career_sources) == 1
    assert detail.career_sources[0].source_type == "Lever"
    assert "api.lever.co" in detail.career_sources[0].api_endpoint

    # 2. List companies
    companies = list_companies(db=test_db, industry="Pharma Tech")
    assert len(companies) >= 1
    assert any(c.name == "AmpleLogic Pharma Tech" for c in companies)

    # 3. Search companies
    search_res = list_companies(db=test_db, search="Hyderabad")
    assert len(search_res) >= 1

    # 4. Get Company Detail
    comp_detail = get_company_detail(company_id=detail.id, db=test_db)
    assert comp_detail.id == detail.id
    assert comp_detail.total_active_jobs == 0

    # 5. Update Company
    update_data = CompanyUpdate(description="Updated GMP and LIMS software provider")
    updated = update_company(company_id=detail.id, payload=update_data, db=test_db)
    assert updated.description == "Updated GMP and LIMS software provider"

    # 6. Add Career Source
    source_payload = CompanyCareerSourceCreate(
        source_type="Direct",
        base_url="https://amplelogic.com/careers",
        career_url="https://amplelogic.com/careers"
    )
    new_src = add_company_career_source(company_id=detail.id, payload=source_payload, db=test_db)
    assert new_src.source_type == "Direct"

    # 7. Get Stats Summary
    stats = get_company_stats(db=test_db)
    assert stats["total_companies"] >= 1
    assert "Pharma Tech" in stats["industry_breakdown"]

    # 8. List Global Job Sources
    job_src = JobSource(name="LinkedIn Test", source_type="portal_api", base_url="https://linkedin.com")
    test_db.add(job_src)
    test_db.commit()
    all_job_sources = list_global_job_sources(db=test_db)
    assert len(all_job_sources) >= 1

    # 9. Trigger Discovery Cycle via API
    disc_query = CompanyDiscoveryQuery(keyword="Piramal")
    disc_result = trigger_company_discovery(query=disc_query, db=test_db)
    assert disc_result.new_companies_added >= 1
    assert any(c.name == "Piramal Pharma Solutions" for c in disc_result.companies)

