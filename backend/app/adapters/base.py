from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseATSAdapter(ABC):
    """Abstract base class for Applicant Tracking System (ATS) adapters."""

    name: str = "BaseATS"

    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if this adapter can handle the given career URL."""
        pass

    @classmethod
    @abstractmethod
    def detect_api_endpoint(cls, url: str) -> Optional[str]:
        """Detect and construct public JSON or REST API endpoint if available."""
        pass

    @classmethod
    @abstractmethod
    def get_source_type(cls) -> str:
        """Return canonical source type name (e.g. Workday, Greenhouse, Lever, Direct)."""
        pass

