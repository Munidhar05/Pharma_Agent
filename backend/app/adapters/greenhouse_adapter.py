import re
from typing import Optional
from urllib.parse import urlparse
from backend.app.adapters.base import BaseATSAdapter


class GreenhouseAdapter(BaseATSAdapter):
    """
    Adapter for Greenhouse ATS (used by modern Biotech, Genomics, and Pharma Tech companies).
    Detects `boards.greenhouse.io` URLs and constructs public API endpoints.
    """

    name: str = "Greenhouse"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        if not url:
            return False
        return "greenhouse.io" in url.lower()

    @classmethod
    def detect_api_endpoint(cls, url: str) -> Optional[str]:
        """
        Translates `https://boards.greenhouse.io/biotechco`
        into `https://boards-api.greenhouse.io/v1/boards/biotechco/jobs?content=true`
        """
        if not cls.can_handle(url):
            return None

        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        board_token = path_parts[0] if path_parts else None

        if board_token:
            return f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        return None

    @classmethod
    def get_source_type(cls) -> str:
        return "Greenhouse"

