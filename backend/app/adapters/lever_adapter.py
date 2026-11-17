from typing import Optional
from urllib.parse import urlparse
from backend.app.adapters.base import BaseATSAdapter


class LeverAdapter(BaseATSAdapter):
    """
    Adapter for Lever ATS (used by agile Life Sciences SaaS and Tech startups).
    Detects `jobs.lever.co` URLs and constructs public API endpoints.
    """

    name: str = "Lever"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        if not url:
            return False
        return "lever.co" in url.lower()

    @classmethod
    def detect_api_endpoint(cls, url: str) -> Optional[str]:
        """
        Translates `https://jobs.lever.co/company`
        into `https://api.lever.co/v0/postings/company?mode=json`
        """
        if not cls.can_handle(url):
            return None

        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        company = path_parts[0] if path_parts else None

        if company:
            return f"https://api.lever.co/v0/postings/{company}?mode=json"
        return None

    @classmethod
    def get_source_type(cls) -> str:
        return "Lever"

