from backend.app.database import Base
from backend.app.models.user import User, UserPreferences
from backend.app.models.candidate import (
    CandidateProfile,
    CandidateSkill,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    CandidateResume,
)
from backend.app.models.company import Company, CompanyCareerSource, JobSource
from backend.app.models.job import DiscoveredJob, JobRequirement, JobSkill
from backend.app.models.matching import JobMatchResult
from backend.app.models.resume import GeneratedResume
from backend.app.models.application import ApplicationRecord, ApplicationEvent
from backend.app.models.audit import Notification, AgentExecutionLog, SearchHistory

__all__ = [
    "Base",
    "User",
    "UserPreferences",
    "CandidateProfile",
    "CandidateSkill",
    "CandidateEducation",
    "CandidateExperience",
    "CandidateProject",
    "CandidateResume",
    "Company",
    "CompanyCareerSource",
    "JobSource",
    "DiscoveredJob",
    "JobRequirement",
    "JobSkill",
    "JobMatchResult",
    "GeneratedResume",
    "ApplicationRecord",
    "ApplicationEvent",
    "Notification",
    "AgentExecutionLog",
    "SearchHistory",
]
