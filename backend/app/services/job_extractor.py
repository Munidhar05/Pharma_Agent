import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from backend.app.services.resume_parser import SKILL_TAXONOMY

INDIAN_CITIES = [
    "Hyderabad", "Bengaluru", "Bangalore", "Chennai", "Pune", "Mumbai", "Navi Mumbai",
    "Ahmedabad", "Noida", "Gurugram", "Gurgaon", "Delhi", "Kolkata", "Visakhapatnam",
    "Chandigarh", "Kochi", "Cochin", "Thane", "Mohali", "Trivandrum", "Vadodara"
]


class JobExtractorService:
    """
    Service to extract structured job metadata from raw job descriptions,
    categorize technical roles, evaluate experience bounds, and generate canonical UIDs.
    """

    @classmethod
    def generate_job_uid(cls, company_slug: str, title: str, req_id: Optional[str], canonical_url: str) -> str:
        """Create a deterministic SHA-256 hash string for deduplicating job vacancies."""
        components = [
            company_slug.strip().lower(),
            re.sub(r"[^a-z0-9]+", "", title.lower()),
            (req_id or "").strip().lower(),
            cls._clean_url(canonical_url)
        ]
        seed = "|".join(components)
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def _clean_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.netloc}{parsed.path}".rstrip("/")

    @classmethod
    def classify_category(cls, title: str, description: str) -> str:
        """
        Classifies job into one of the 7 core pillars:
        - Data Engineering
        - Data Analytics
        - AI and Machine Learning
        - Database and SQL
        - Clinical and Pharmaceutical Data
        - Pharma IT and Data Quality
        - Other Technical
        """
        combined = f"{title} {description}".lower()

        # 1. Clinical and Pharmaceutical Data
        if any(term in combined for term in [
            "clinical data", "clinical database", "cdisc", "sdtm", "adam", "pharmacovigilance",
            "drug safety", "real world data", "real world evidence", "lims", "bioinformatics"
        ]):
            return "Clinical and Pharmaceutical Data"

        # 2. Pharma IT and Data Quality / CSV
        if any(term in combined for term in [
            "computer system validation", "csv engineer", "gxp", "data quality", "data governance",
            "data steward", "master data management", "21 cfr part 11", "mes data"
        ]):
            return "Pharma IT and Data Quality"

        # 3. AI and Machine Learning
        if any(term in combined for term in [
            "ai engineer", "machine learning", "nlp", "generative ai", "rag", "data scientist",
            "clinical ai", "llm developer"
        ]):
            return "AI and Machine Learning"

        # 4. Data Engineering
        if any(term in combined for term in [
            "data engineer", "etl", "elt", "pyspark", "spark", "databricks", "snowflake",
            "dbt", "big data", "data pipeline", "analytics engineer", "fabric"
        ]):
            return "Data Engineering"

        # 5. Database and SQL
        if any(term in combined for term in [
            "sql developer", "database developer", "database engineer", "dba", "data warehouse",
            "postgresql developer", "oracle developer"
        ]):
            return "Database and SQL"

        # 6. Data Analytics
        if any(term in combined for term in [
            "data analyst", "business intelligence", "bi analyst", "power bi", "tableau",
            "reporting analyst", "mis analyst", "commercial analyst"
        ]):
            return "Data Analytics"

        return "Other Technical"

    @classmethod
    def extract_location_and_mode(cls, text: str) -> Tuple[str, str, str]:
        """Returns (location, city, work_mode: Onsite, Hybrid, Remote)."""
        lower = text.lower()
        
        # Work mode
        work_mode = "Onsite"
        if "remote" in lower or "work from home" in lower:
            work_mode = "Remote"
        elif "hybrid" in lower or "flexible" in lower:
            work_mode = "Hybrid"

        # City detection
        detected_city = "India"
        for city in INDIAN_CITIES:
            if re.search(r"\b" + re.escape(city.lower()) + r"\b", lower):
                detected_city = city
                # Normalize city name
                if detected_city.lower() in ["bangalore"]:
                    detected_city = "Bengaluru"
                elif detected_city.lower() in ["gurgaon"]:
                    detected_city = "Gurugram"
                elif detected_city.lower() in ["cochin"]:
                    detected_city = "Kochi"
                break

        location = f"{detected_city}, India" if detected_city != "India" else "India"
        if work_mode == "Remote" and detected_city == "India":
            location = "Remote India"

        return location, detected_city, work_mode

    @classmethod
    def extract_experience_range(cls, text: str) -> Tuple[float, Optional[float]]:
        """
        Extracts minimum and maximum required experience in years.
        Prefers Freshers and early career (0-2 years).
        """
        lower = text.lower()
        if "fresher" in lower or "entry level" in lower or "graduate trainee" in lower or "intern" in lower:
            return 0.0, 1.0

        # Pattern: "0 to 2 years", "0-2 yrs", "1-3 years"
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", lower)
        if range_match:
            min_exp = float(range_match.group(1))
            max_exp = float(range_match.group(2))
            return min_exp, max_exp

        # Pattern: "2+ years", "min 3 years"
        single_match = re.search(r"(?:min(?:imum)?\s*)?(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)", lower)
        if single_match:
            val = float(single_match.group(1))
            return val, val + 2.0

        return 0.0, 2.0  # Default assumption for early-career pharma data openings

    @classmethod
    def extract_salary_details(cls, text: str) -> Tuple[Optional[float], Optional[float], bool]:
        """
        Extract salary if explicitly disclosed.
        Adheres to Rule 5 & 6: Never invent salary figures, do not hide undisclosed listings.
        """
        # Search for CTC / LPA patterns, e.g. "5 - 8 LPA" or "₹6,00,000 - ₹9,00,000"
        lpa_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|inr)", text, re.IGNORECASE)
        if lpa_match:
            min_val = float(lpa_match.group(1)) * 100000
            max_val = float(lpa_match.group(2)) * 100000
            return min_val, max_val, True

        return None, None, False

    @classmethod
    def extract_skills_and_requirements(cls, description: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extracts skills (mandatory vs preferred) and requirements (Education, Experience, Domain).
        """
        skills = []
        requirements = []
        lower_desc = description.lower()

        # Extract skills matching the taxonomy
        for skill_name, category in SKILL_TAXONOMY.items():
            pattern = r"\b" + re.escape(skill_name.lower()) + r"\b"
            if re.search(pattern, lower_desc):
                # Classify mandatory vs preferred based on proximity to keywords
                is_mandatory = True
                if "preferred" in lower_desc and skill_name.lower() in lower_desc.split("preferred")[-1]:
                    is_mandatory = False

                skills.append({
                    "skill_name": skill_name,
                    "is_mandatory": is_mandatory,
                    "skill_category": category
                })

        # Extract education requirements
        if "b.tech" in lower_desc or "bachelor" in lower_desc or "b.e" in lower_desc:
            requirements.append({
                "req_type": "Mandatory",
                "category": "Education",
                "description": "Bachelor's degree in Computer Science, Information Technology, Biotechnology or related technical field."
            })
        if "m.tech" in lower_desc or "master" in lower_desc or "m.sc" in lower_desc:
            requirements.append({
                "req_type": "Preferred",
                "category": "Education",
                "description": "Master's degree in Data Science, Bioinformatics or Life Sciences Informatics."
            })

        return skills, requirements

