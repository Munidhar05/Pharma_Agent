from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session

from backend.app.models import DiscoveredJob, JobRequirement, JobSkill, Company
from backend.app.services.job_extractor import JobExtractorService


class JobExtractionAgent:
    """
    Agent 3: Job Extraction Agent
    Processes unstructured job postings, applies semantic categorization, extracts
    mandatory/preferred competencies and qualifications, and normalizes them into structured records.
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_and_structure_job(
        self,
        raw_job: Dict[str, Any],
        company: Company,
        source_id: Optional[int] = None
    ) -> DiscoveredJob:
        """
        Transforms raw job payload into structured DiscoveredJob with linked JobRequirement and JobSkill records.
        """
        title = raw_job.get("title", "Technical Data Specialist")
        raw_desc = raw_job.get("description", "")
        req_id = raw_job.get("req_id")
        official_url = raw_job.get("official_url") or raw_job.get("canonical_url") or company.careers_url or "https://careers.pharma.internal"
        canonical_url = raw_job.get("canonical_url") or official_url

        # Generate unique canonical UID for deduplication
        job_uid = JobExtractorService.generate_job_uid(
            company_slug=company.slug,
            title=title,
            req_id=req_id,
            canonical_url=canonical_url
        )

        # 1. Semantic category classification
        category = raw_job.get("category") or JobExtractorService.classify_category(title, raw_desc)

        # 2. Location & Work mode
        loc_str = raw_job.get("location") or raw_desc
        location, city, work_mode = JobExtractorService.extract_location_and_mode(loc_str)

        # 3. Experience bounds
        min_exp, max_exp = JobExtractorService.extract_experience_range(raw_desc)

        # 4. Salary disclosure
        sal_min, sal_max, disclosed = JobExtractorService.extract_salary_details(raw_desc)

        # 5. Extract Skills and Requirements
        extracted_skills, extracted_reqs = JobExtractorService.extract_skills_and_requirements(raw_desc)

        # Build DiscoveredJob instance
        job = DiscoveredJob(
            job_uid=job_uid,
            company_id=company.id,
            source_id=source_id,
            title=title,
            req_id=req_id,
            category=category,
            location=location,
            city=city,
            work_mode=raw_job.get("work_mode") or work_mode,
            employment_type=raw_job.get("employment_type", "Full-time"),
            min_experience=min_exp,
            max_experience=max_exp,
            education_requirements=raw_job.get("education", "B.Tech / M.Sc / MCA"),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency="INR",
            salary_disclosed=disclosed,
            description=raw_desc,
            official_application_url=official_url,
            canonical_url=canonical_url,
            status="ACTIVE",
            first_discovered_at=datetime.utcnow(),
            last_verified_at=datetime.utcnow()
        )

        # Attach requirements
        for req in extracted_reqs:
            job.requirements.append(JobRequirement(
                req_type=req["req_type"],
                category=req["category"],
                description=req["description"]
            ))

        # Attach skills
        for sk in extracted_skills:
            job.skills.append(JobSkill(
                skill_name=sk["skill_name"],
                is_mandatory=sk["is_mandatory"],
                skill_category=sk["skill_category"]
            ))

        return job

