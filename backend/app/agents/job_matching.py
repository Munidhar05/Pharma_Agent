import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models import (
    CandidateProfile,
    DiscoveredJob,
    JobMatchResult,
    UserPreferences,
    Notification,
    AgentExecutionLog
)
from backend.app.services.scoring_engine import ScoringEngineService


class JobMatchingAgent:
    """
    Agent 6: Job Matching Agent
    Autonomous AI agent evaluating candidate profile eligibility against discovered active jobs,
    calculating multi-dimensional match scores, recording gap analyses, and alerting candidates.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_candidate_for_job(
        self,
        candidate: CandidateProfile,
        job: DiscoveredJob,
        preferences: Optional[UserPreferences] = None
    ) -> JobMatchResult:
        """
        Calculates match score between a candidate and a specific job,
        persisting or updating the JobMatchResult record.
        """
        # Execute scoring engine
        eval_result = ScoringEngineService.evaluate_match(
            candidate=candidate,
            job=job,
            preferences=preferences
        )

        # Check for existing match record
        match_record = self.db.query(JobMatchResult).filter(
            JobMatchResult.profile_id == candidate.id,
            JobMatchResult.job_id == job.id
        ).first()

        if not match_record:
            match_record = JobMatchResult(
                profile_id=candidate.id,
                job_id=job.id,
                overall_score=eval_result["overall_score"],
                skills_score=eval_result["skills_score"],
                experience_score=eval_result["experience_score"],
                education_score=eval_result["education_score"],
                responsibility_score=eval_result["responsibility_score"],
                industry_score=eval_result["industry_score"],
                location_score=eval_result["location_score"],
                eligibility_label=eval_result["eligibility_label"],
                is_hard_eligible=eval_result["is_hard_eligible"],
                matched_skills=eval_result["matched_skills"],
                partially_matched_skills=eval_result["partially_matched_skills"],
                missing_skills=eval_result["missing_skills"],
                rejection_reasons=eval_result["rejection_reasons"],
                recommended_action=eval_result["recommended_action"],
                evaluated_at=datetime.utcnow()
            )
            self.db.add(match_record)
        else:
            match_record.overall_score = eval_result["overall_score"]
            match_record.skills_score = eval_result["skills_score"]
            match_record.experience_score = eval_result["experience_score"]
            match_record.education_score = eval_result["education_score"]
            match_record.responsibility_score = eval_result["responsibility_score"]
            match_record.industry_score = eval_result["industry_score"]
            match_record.location_score = eval_result["location_score"]
            match_record.eligibility_label = eval_result["eligibility_label"]
            match_record.is_hard_eligible = eval_result["is_hard_eligible"]
            match_record.matched_skills = eval_result["matched_skills"]
            match_record.partially_matched_skills = eval_result["partially_matched_skills"]
            match_record.missing_skills = eval_result["missing_skills"]
            match_record.rejection_reasons = eval_result["rejection_reasons"]
            match_record.recommended_action = eval_result["recommended_action"]
            match_record.evaluated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(match_record)

        # Trigger notification if strong match
        alert_threshold = preferences.min_match_score_alert if preferences else 75
        if match_record.overall_score >= alert_threshold and match_record.is_hard_eligible:
            self._dispatch_match_notification(candidate=candidate, job=job, match=match_record)

        return match_record

    def evaluate_all_active_jobs(
        self,
        candidate: CandidateProfile,
        preferences: Optional[UserPreferences] = None,
        category: Optional[str] = None,
        freshers_only: bool = False
    ) -> Dict[str, Any]:
        """
        Batch evaluates all active vacancies against candidate profile,
        ranking the best matches.
        """
        execution_id = f"match_eval_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        query = self.db.query(DiscoveredJob).filter(DiscoveredJob.status == "ACTIVE")
        if category:
            query = query.filter(DiscoveredJob.category.ilike(f"%{category}%"))
        if freshers_only:
            query = query.filter(DiscoveredJob.min_experience <= 0.0)

        active_jobs = query.all()
        evaluated_matches = []
        strong_matches_count = 0
        eligible_jobs_count = 0

        for job in active_jobs:
            match = self.evaluate_candidate_for_job(
                candidate=candidate,
                job=job,
                preferences=preferences
            )
            evaluated_matches.append(match)
            if match.is_hard_eligible:
                eligible_jobs_count += 1
            if match.overall_score >= 80.0 and match.is_hard_eligible:
                strong_matches_count += 1

        # Sort by overall score descending
        evaluated_matches.sort(key=lambda m: m.overall_score, reverse=True)

        # Record agent execution log
        log = AgentExecutionLog(
            agent_name="JobMatchingAgent",
            execution_id=execution_id,
            task_type="BatchJobMatching",
            status="SUCCESS",
            items_processed=len(active_jobs),
            items_failed=0,
            metadata_json={
                "candidate_id": candidate.id,
                "eligible_count": eligible_jobs_count,
                "strong_matches": strong_matches_count
            },
            start_time=start_time,
            end_time=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

        return {
            "execution_id": execution_id,
            "total_jobs_evaluated": len(active_jobs),
            "eligible_jobs_count": eligible_jobs_count,
            "strong_matches_count": strong_matches_count,
            "matches": evaluated_matches
        }

    def _dispatch_match_notification(
        self,
        candidate: CandidateProfile,
        job: DiscoveredJob,
        match: JobMatchResult
    ) -> None:
        """Create dashboard notification for high-scoring job opportunity."""
        # Avoid duplicate notifications for same job
        existing_notif = self.db.query(Notification).filter(
            Notification.user_id == candidate.user_id,
            Notification.title.ilike(f"%{job.company.name}%{job.title[:20]}%")
        ).first()

        if not existing_notif:
            missing_names = ", ".join([m["skill"] for m in match.missing_skills[:2]]) or "None"
            notif = Notification(
                user_id=candidate.user_id,
                title=f"STRONG MATCH: {job.company.name} - {job.title}",
                message=(
                    f"A new data position was matched at {job.company.name} in {job.city}.\n"
                    f"Match Score: {match.overall_score}% ({match.eligibility_label}).\n"
                    f"Missing skills: {missing_names}.\n"
                    f"Recommended Action: {match.recommended_action}"
                ),
                notification_type="StrongMatch",
                channel="dashboard",
                is_read=False
            )
            self.db.add(notif)
            self.db.commit()

