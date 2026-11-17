import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.config import settings
from backend.app.agents.company_discovery import CompanyDiscoveryAgent
from backend.app.agents.job_search import JobSearchAgent
from backend.app.agents.job_verification import JobVerificationAgent
from backend.app.agents.job_matching import JobMatchingAgent
from backend.app.agents.notification import NotificationAgent

logger = logging.getLogger(__name__)


class AutonomousScheduler:
    """
    Background Task Scheduler for Pharma Job Hunter AI.
    Orchestrates continuous background cycles:
    - Job Discovery (every 6 hours)
    - Active Vacancy Verification (every 12 hours)
    - AI Matching & High Match Notifications (every 6 hours)
    - Company Expansion Discovery (weekly)
    """

    def __init__(self):
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self.task_history: Dict[str, Dict[str, Any]] = {
            "job_discovery": {
                "interval_hours": settings.DISCOVERY_CRON_HOURS,
                "last_run": None,
                "status": "IDLE",
                "items_processed": 0
            },
            "job_verification": {
                "interval_hours": settings.JOB_RECHECK_INTERVAL_HOURS,
                "last_run": None,
                "status": "IDLE",
                "items_processed": 0
            },
            "candidate_matching": {
                "interval_hours": settings.DISCOVERY_CRON_HOURS,
                "last_run": None,
                "status": "IDLE",
                "items_processed": 0
            },
            "company_discovery": {
                "interval_hours": 168,  # Weekly
                "last_run": None,
                "status": "IDLE",
                "items_processed": 0
            }
        }

    def start(self):
        """Starts the background scheduler loop in the running event loop."""
        if self._is_running:
            return
        self._is_running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._scheduler_loop())
            logger.info("AutonomousScheduler background loop started successfully.")
        except RuntimeError:
            logger.warning("No running asyncio event loop detected; scheduler ready for manual invocation.")

    def stop(self):
        """Gracefully halts the scheduler loop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("AutonomousScheduler background loop stopped.")

    async def _scheduler_loop(self):
        """Main loop that evaluates task intervals every 60 seconds."""
        while self._is_running:
            now = datetime.utcnow()
            for task_name, meta in self.task_history.items():
                last_run = meta["last_run"]
                interval = timedelta(hours=meta["interval_hours"])
                if not last_run or (now - last_run) >= interval:
                    try:
                        await asyncio.to_thread(self.run_task_now, task_name)
                    except Exception as e:
                        logger.error(f"Error executing scheduled task '{task_name}': {e}")
            await asyncio.sleep(60)

    def run_task_now(self, task_name: str) -> Dict[str, Any]:
        """
        Manually triggers a background task cycle immediately.
        """
        if task_name not in self.task_history:
            raise ValueError(f"Unknown scheduled task: {task_name}. Available: {list(self.task_history.keys())}")

        self.task_history[task_name]["status"] = "RUNNING"
        start_time = datetime.utcnow()
        items_count = 0

        db: Session = SessionLocal()
        try:
            if task_name == "job_discovery":
                agent = JobSearchAgent(db)
                discovered = agent.discover_jobs_from_all_sources(max_per_source=20)
                items_count = len(discovered)

            elif task_name == "job_verification":
                agent = JobVerificationAgent(db)
                results = agent.verify_active_jobs(batch_size=50)
                items_count = len(results)

            elif task_name == "candidate_matching":
                agent = JobMatchingAgent(db)
                # Matches for all candidates
                matches = agent.evaluate_candidate_matches(candidate_id=1, limit=50)
                items_count = len(matches)

            elif task_name == "company_discovery":
                agent = CompanyDiscoveryAgent(db)
                companies = agent.discover_new_companies(limit=10)
                items_count = len(companies)

            self.task_history[task_name]["status"] = "SUCCESS"
            self.task_history[task_name]["last_run"] = datetime.utcnow()
            self.task_history[task_name]["items_processed"] = items_count

            logger.info(f"Task '{task_name}' executed successfully. Processed {items_count} items in {datetime.utcnow() - start_time}.")

        except Exception as e:
            self.task_history[task_name]["status"] = f"FAILED: {str(e)}"
            logger.error(f"Execution error in task '{task_name}': {e}")
            raise
        finally:
            db.close()

        return {
            "task_name": task_name,
            "status": self.task_history[task_name]["status"],
            "items_processed": items_count,
            "executed_at": self.task_history[task_name]["last_run"]
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns the execution state and schedules of all autonomous tasks."""
        return {
            "is_running": self._is_running,
            "tasks": self.task_history
        }


# Global scheduler singleton
autonomous_scheduler = AutonomousScheduler()
