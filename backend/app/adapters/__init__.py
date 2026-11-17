from typing import Tuple, Optional
from backend.app.adapters.base import BaseATSAdapter
from backend.app.adapters.workday_adapter import WorkdayAdapter
from backend.app.adapters.greenhouse_adapter import GreenhouseAdapter
from backend.app.adapters.lever_adapter import LeverAdapter
from backend.app.adapters.direct_adapter import DirectAdapter

ADAPTERS = [
    WorkdayAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    DirectAdapter,
]


def detect_career_source_type(career_url: str) -> Tuple[str, Optional[str]]:
    """
    Inspect career URL and return (source_type, api_endpoint).
    Iterates through registered adapters to determine ATS platform.
    """
    if not career_url:
        return "Direct", None

    for adapter in ADAPTERS:
        if adapter.can_handle(career_url):
            endpoint = adapter.detect_api_endpoint(career_url)
            return adapter.get_source_type(), endpoint

    return "Direct", None


__all__ = [
    "BaseATSAdapter",
    "WorkdayAdapter",
    "GreenhouseAdapter",
    "LeverAdapter",
    "DirectAdapter",
    "detect_career_source_type",
]

