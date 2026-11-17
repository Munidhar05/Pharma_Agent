import re
from typing import Optional
from urllib.parse import urlparse
from backend.app.adapters.base import BaseATSAdapter


class WorkdayAdapter(BaseATSAdapter):
    """
    Adapter for Workday ATS portals (widely used by Pfizer, Roche, Novartis, Sanofi, GSK, BMS, AbbVie).
    Detects `myworkdayjobs.com` URLs and constructs public client experience search API endpoints.
    """

    name: str = "Workday"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        if not url:
            return False
        return "myworkdayjobs.com" in url.lower() or "workday" in url.lower()

    @classmethod
    def detect_api_endpoint(cls, url: str) -> Optional[str]:
        """
        Translates a public Workday career page URL:
        https://pfizer.wd1.myworkdayjobs.com/PfizerCareers
        into its public JSON search endpoint:
        https://pfizer.wd1.myworkdayjobs.com/wday/cxs/pfizer/PfizerCareers/jobs
        """
        if not cls.can_handle(url):
            return None

        parsed = urlparse(url)
        host = parsed.netloc
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        # Standard Workday host pattern: <tenant>.<instance>.myworkdayjobs.com
        tenant_match = re.match(r"^([a-zA-Z0-9_-]+)", host)
        tenant = tenant_match.group(1) if tenant_match else "company"
        
        # Site name is typically the first or last path component (e.g. PfizerCareers, roche-ext)
        site = path_parts[0] if path_parts else "External"

        return f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    @classmethod
    def get_source_type(cls) -> str:
        return "Workday"

