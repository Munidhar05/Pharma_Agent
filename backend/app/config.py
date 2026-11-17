from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

# Base project path
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core App
    APP_NAME: str = "Pharma Job Hunter AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "pharma-job-hunter-insecure-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite:///./pharma_jobs.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI / LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # File Storage
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    RESUME_OUTPUT_DIR: str = str(BASE_DIR / "generated_resumes")

    # Business Rules & Thresholds
    JOB_FRESHNESS_DAYS: int = 7
    JOB_RECHECK_INTERVAL_HOURS: int = 12
    DISCOVERY_CRON_HOURS: int = 6

    # Scoring Weights (Total 100%)
    WEIGHT_TECHNICAL_SKILLS: float = 0.30
    WEIGHT_EXPERIENCE: float = 0.20
    WEIGHT_EDUCATION: float = 0.15
    WEIGHT_RESPONSIBILITIES: float = 0.15
    WEIGHT_INDUSTRY: float = 0.10
    WEIGHT_LOCATION_PREF: float = 0.10

    # Automation Mode
    APPLICATION_MODE: str = "Assisted application with approval"
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT_MS: int = 30000

    # Notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "noreply@pharmajobhunter.ai"
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    def setup_directories(self) -> None:
        """Ensure necessary storage directories exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.RESUME_OUTPUT_DIR, exist_ok=True)


settings = Settings()
settings.setup_directories()

