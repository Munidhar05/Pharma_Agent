import uuid
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models import Company, CompanyCareerSource, AgentExecutionLog, Notification
from backend.app.services.career_discovery import CareerDiscoveryService

# Registry of high-growth pharmaceutical, biotech, and life science companies in India for continuous expansion
EXPANSION_COMPANY_REGISTRY = [
    {
        "name": "Aragen Life Sciences",
        "industry": "CRO & Clinical Research",
        "hq": "Hyderabad",
        "careers": "https://www.aragen.com/careers",
        "description": "Leading R&D and manufacturing solutions provider for life sciences."
    },
    {
        "name": "Suven Life Sciences",
        "industry": "Indian Pharma",
        "hq": "Hyderabad",
        "careers": "https://www.suven.com/careers",
        "description": "Biopharmaceutical company focused on neurodegenerative diseases."
    },
    {
        "name": "Piramal Pharma Solutions",
        "industry": "Indian Pharma",
        "hq": "Mumbai",
        "careers": "https://www.piramalpharmasolutions.com/careers",
        "description": "Global CDMO offering end-to-end development and manufacturing."
    },
    {
        "name": "Alkem Laboratories",
        "industry": "Indian Pharma",
        "hq": "Mumbai",
        "careers": "https://www.alkemlabs.com/careers",
        "description": "Indian multinational pharmaceutical company."
    },
    {
        "name": "Cadila Pharmaceuticals",
        "industry": "Indian Pharma",
        "hq": "Ahmedabad",
        "careers": "https://www.cadilapharma.com/careers",
        "description": "One of the largest privately-held pharma companies in India."
    },
    {
        "name": "Alembic Pharmaceuticals",
        "industry": "Indian Pharma",
        "hq": "Vadodara",
        "careers": "https://www.alembicpharmaceuticals.com/careers",
        "description": "Indian pharmaceutical company manufacturing generic drugs."
    },
    {
        "name": "Micro Labs",
        "industry": "Indian Pharma",
        "hq": "Bengaluru",
        "careers": "https://www.microlabsltd.com/careers",
        "description": "Leading pharmaceutical manufacturing enterprise."
    },
    {
        "name": "Wockhardt",
        "industry": "Indian Pharma",
        "hq": "Mumbai",
        "careers": "https://www.wockhardt.com/careers",
        "description": "Global pharmaceutical and biotechnology company."
    },
    {
        "name": "Enzene Biosciences",
        "industry": "Biotech & Life Sciences",
        "hq": "Pune",
        "careers": "https://www.enzene.com/careers",
        "description": "Technology driven biopharmaceutical company."
    },
    {
        "name": "Anthem Biosciences",
        "industry": "CRO & Clinical Research",
        "hq": "Bengaluru",
        "careers": "https://anthembio.com/careers",
        "description": "Contract Research and Innovation Service Provider."
    },
    {
        "name": "Mapmygenome",
        "industry": "Biotech & Life Sciences",
        "hq": "Hyderabad",
        "careers": "https://mapmygenome.in/careers",
        "description": "Molecular diagnostics and genomics company."
    },
    {
        "name": "Saama Technologies",
        "industry": "Pharma Tech",
        "hq": "Pune",
        "careers": "https://jobs.lever.co/saama",
        "description": "AI-powered clinical data analytics platform."
    },
    {
        "name": "Aetion Healthcare",
        "industry": "Pharma Tech",
        "hq": "Bengaluru",
        "careers": "https://boards.greenhouse.io/aetion",
        "description": "Real-world evidence platform for life sciences."
    }
]


class CompanyDiscoveryAgent:
    """
    Agent 1: Company Discovery Agent
    Autonomous agent responsible for discovering new pharmaceutical, biotech, CRO, and life science companies
    in India, classifying their domain, detecting their career ATS endpoints, and maintaining the dynamic database.
    """

    def __init__(self, db: Session):
        self.db = db

    def slugify(self, text: str) -> str:
        """Create URL-friendly slug from company name."""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def run_discovery_cycle(
        self,
        keyword: Optional[str] = None,
        industry_category: Optional[str] = None,
        auto_detect_ats: bool = True
    ) -> Dict[str, Any]:
        """
        Execute an autonomous company discovery cycle:
        1. Probes the expansion registry and dynamic sources.
        2. Deduplicates against existing companies.
        3. Analyzes career portals and identifies ATS platform.
        4. Persists new companies and career sources.
        5. Logs audit trail in `agent_execution_logs`.
        """
        execution_id = f"comp_disc_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        new_companies = []
        sources_detected = 0
        items_processed = 0

        try:
            for item in EXPANSION_COMPANY_REGISTRY:
                # Apply optional keyword/industry filters
                if keyword and keyword.lower() not in item["name"].lower():
                    continue
                if industry_category and industry_category.lower() != item["industry"].lower():
                    continue

                items_processed += 1
                slug = self.slugify(item["name"])

                # Check if company already exists
                existing = self.db.query(Company).filter(
                    (Company.slug == slug) | (Company.name.ilike(item["name"]))
                ).first()

                if existing:
                    # Update career URL or verify sources if missing
                    if item.get("careers") and not existing.careers_url:
                        existing.careers_url = item["careers"]
                        self.db.commit()
                    continue

                # Analyze career source
                career_analysis = CareerDiscoveryService.analyze_company_career(
                    company_name=item["name"],
                    career_url=item.get("careers", "")
                )

                # Create company record
                company = Company(
                    name=item["name"],
                    slug=slug,
                    industry_category=item.get("industry") or CareerDiscoveryService.infer_industry_category(item["name"]),
                    website=f"https://www.{slug}.com",
                    careers_url=career_analysis["career_url"],
                    hq_location=item.get("hq", "India"),
                    description=item.get("description"),
                    is_active=True
                )
                self.db.add(company)
                self.db.flush()

                # Add detected career source
                if career_analysis["career_url"]:
                    source_rec = CompanyCareerSource(
                        company_id=company.id,
                        source_type=career_analysis["source_type"],
                        base_url=career_analysis["career_url"],
                        career_url=career_analysis["career_url"],
                        api_endpoint=career_analysis["api_endpoint"],
                        is_active=True
                    )
                    self.db.add(source_rec)
                    sources_detected += 1

                new_companies.append(company)

            self.db.commit()

            # Record agent execution log
            log = AgentExecutionLog(
                agent_name="CompanyDiscoveryAgent",
                execution_id=execution_id,
                task_type="CompanyDiscoveryCycle",
                status="SUCCESS",
                items_processed=items_processed,
                items_failed=0,
                metadata_json={
                    "new_companies_count": len(new_companies),
                    "sources_detected": sources_detected,
                    "keyword_filter": keyword,
                    "industry_filter": industry_category
                },
                start_time=start_time,
                end_time=datetime.utcnow()
            )
            self.db.add(log)
            self.db.commit()

            return {
                "execution_id": execution_id,
                "items_processed": items_processed,
                "new_companies_added": len(new_companies),
                "sources_detected": sources_detected,
                "new_companies": new_companies
            }

        except Exception as e:
            self.db.rollback()
            log = AgentExecutionLog(
                agent_name="CompanyDiscoveryAgent",
                execution_id=execution_id,
                task_type="CompanyDiscoveryCycle",
                status="FAILED",
                items_processed=items_processed,
                items_failed=1,
                error_details={"error": str(e)},
                start_time=start_time,
                end_time=datetime.utcnow()
            )
            self.db.add(log)
            self.db.commit()
            raise e

