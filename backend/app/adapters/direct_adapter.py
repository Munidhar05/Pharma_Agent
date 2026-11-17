from typing import Optional
from backend.app.adapters.base import BaseATSAdapter


class DirectAdapter(BaseATSAdapter):
    """
    Fallback adapter for Direct Corporate Career Portals (e.g. Cipla, Dr. Reddy's, Aurobindo, Sun Pharma).
    Handles standard career URLs, parsing HTML listings while strictly obeying robots.txt and rate limits.
    """

    name: str = "Direct"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        return True  # Fallback handler

    @classmethod
    def detect_api_endpoint(cls, url: str) -> Optional[str]:
        return None  # Direct portals use HTML parsing or internal feeds

    @classmethod
    def get_source_type(cls) -> str:
        return "Direct"

