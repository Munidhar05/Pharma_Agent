import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from backend.app.adapters import detect_career_source_type


class CareerDiscoveryService:
    """Service to discover, validate, and classify company career sources and ATS platforms."""

    PHARMA_KEYWORDS = [
        "pharma", "pharmaceutical", "laboratories", "lab", "therapeutics", "drugs", "biotech", "life sciences",
        "clinical", "cro", "cdmo", "biologics", "genomics", "healthcare", "bio"
    ]

    @staticmethod
    def normalize_url(url: str) -> str:
        """Ensure standard https:// prefix and clean trailing slashes."""
        if not url:
            return ""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        return url.rstrip("/")

    @classmethod
    def analyze_company_career(cls, company_name: str, career_url: str) -> Dict[str, Any]:
        """
        Analyze a company's career URL:
        - Normalizes URL
        - Detects ATS platform (Workday, Greenhouse, Lever, Direct)
        - Discovers API endpoint if available
        - Infers industry category if ambiguous
        """
        clean_url = cls.normalize_url(career_url)
        source_type, api_endpoint = detect_career_source_type(clean_url)

        return {
            "company_name": company_name,
            "career_url": clean_url,
            "source_type": source_type,
            "api_endpoint": api_endpoint,
            "is_valid": bool(clean_url and urlparse(clean_url).netloc)
        }

    @classmethod
    def infer_industry_category(cls, company_name: str, description: Optional[str] = None) -> str:
        """
        Classifies company into one of the 5 canonical categories:
        - Indian Pharma
        - Global Pharma
        - CRO & Clinical Research
        - Biotech & Life Sciences
        - Pharma Tech
        """
        text = f"{company_name} {description or ''}".lower()

        # Check CRO
        if any(w in text for w in ["cro", "clinical research", "iqvia", "parexel", "icon", "syneos", "labcorp", "fortrea"]):
            return "CRO & Clinical Research"

        # Check Biotech
        if any(w in text for w in ["biotech", "biologics", "genomics", "serum", "syngene", "medgenome", "bioinformatics"]):
            return "Biotech & Life Sciences"

        # Check Pharma Tech / Software
        if any(w in text for w in ["tech", "software", "veeva", "amplelogic", "indegene", "informatics", "systems", "solutions"]):
            return "Pharma Tech"

        # Check Global Pharma
        if any(w in text for w in ["pfizer", "roche", "novartis", "sanofi", "astrazeneca", "gsk", "lilly", "merck", "bms", "amgen", "abbvie", "bayer"]):
            return "Global Pharma"

        # Default Indian Pharma
        return "Indian Pharma"

