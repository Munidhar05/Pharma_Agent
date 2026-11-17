import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import CandidateProfile, DiscoveredJob, GeneratedResume, AgentExecutionLog
from backend.app.services.resume_builder import ResumeBuilderService
from backend.app.agents.ats_optimization import ATSOptimizationAgent


class ResumeGenerationAgent:
    """
    Agent 8: Resume Generation Agent
    Coordinates ATS optimization and generates clean, standard-layout PDF and DOCX resumes
    saved against the target job in the database.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_tailored_resume(
        self,
        candidate: CandidateProfile,
        job: DiscoveredJob,
        custom_headline: Optional[str] = None,
        custom_summary: Optional[str] = None
    ) -> GeneratedResume:
        """
        Coordinates ATS optimization and dual PDF/DOCX generation:
        1. Invokes Agent 7 (ATSOptimizationAgent) for keyword coverage and content ranking.
        2. Invokes ResumeBuilderService to generate ATS-compliant PDF.
        3. Invokes ResumeBuilderService to generate ATS-compliant DOCX.
        4. Persists GeneratedResume record linked to candidate and job.
        5. Preserves original candidate resumes untouched.
        """
        execution_id = f"resume_gen_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        # Step 1: Run ATS Optimization Agent
        ats_agent = ATSOptimizationAgent(candidate=candidate, job=job)
        coverage_report = ats_agent.generate_coverage_report()
        tailored_content = ats_agent.optimize_resume_content(
            custom_headline=custom_headline,
            custom_summary=custom_summary
        )

        # File paths
        file_prefix = f"resume_candidate_{candidate.id}_job_{job.id}_{uuid.uuid4().hex[:6]}"
        pdf_path = os.path.join(settings.RESUME_OUTPUT_DIR, f"{file_prefix}.pdf")
        docx_path = os.path.join(settings.RESUME_OUTPUT_DIR, f"{file_prefix}.docx")

        contact_info = {
            "email": candidate.user.email if candidate.user else "candidate@pharma.com",
            "phone": candidate.phone,
            "location": candidate.current_location,
            "linkedin": candidate.linkedin_url,
            "github": candidate.github_url
        }

        # Step 2: Build PDF Resume
        ResumeBuilderService.generate_pdf_resume(
            output_path=pdf_path,
            full_name=candidate.user.full_name if candidate.user else "Candidate",
            contact_info=contact_info,
            headline=tailored_content.headline,
            summary=tailored_content.summary,
            skills=tailored_content.selected_skills,
            education=tailored_content.education,
            projects=tailored_content.selected_projects
        )

        # Step 3: Build DOCX Resume
        ResumeBuilderService.generate_docx_resume(
            output_path=docx_path,
            full_name=candidate.user.full_name if candidate.user else "Candidate",
            contact_info=contact_info,
            headline=tailored_content.headline,
            summary=tailored_content.summary,
            skills=tailored_content.selected_skills,
            education=tailored_content.education,
            projects=tailored_content.selected_projects
        )

        # Step 4: Persist or update GeneratedResume record
        existing = self.db.query(GeneratedResume).filter(
            GeneratedResume.profile_id == candidate.id,
            GeneratedResume.job_id == job.id
        ).first()

        title = f"{job.company.name if job.company else 'Pharma'} - {job.title} ATS Resume"

        matched_list = [
            {"keyword": item.keyword, "evidence": item.candidate_evidence}
            for item in coverage_report.items if item.status == "Matched"
        ]
        missing_list = [
            {"keyword": item.keyword, "importance": item.importance}
            for item in coverage_report.items if item.status == "Missing"
        ]

        if not existing:
            resume_record = GeneratedResume(
                profile_id=candidate.id,
                job_id=job.id,
                title=title,
                file_path_pdf=pdf_path,
                file_path_docx=docx_path,
                keyword_coverage_score=coverage_report.coverage_percentage,
                matched_keywords=matched_list,
                missing_keywords=missing_list,
                tailored_headline=tailored_content.headline,
                tailored_summary=tailored_content.summary,
                selected_projects=tailored_content.selected_projects,
                selected_skills=tailored_content.selected_skills,
                is_approved_by_user=False,
                generated_at=datetime.utcnow()
            )
            self.db.add(resume_record)
        else:
            resume_record = existing
            resume_record.title = title
            resume_record.file_path_pdf = pdf_path
            resume_record.file_path_docx = docx_path
            resume_record.keyword_coverage_score = coverage_report.coverage_percentage
            resume_record.matched_keywords = matched_list
            resume_record.missing_keywords = missing_list
            resume_record.tailored_headline = tailored_content.headline
            resume_record.tailored_summary = tailored_content.summary
            resume_record.selected_projects = tailored_content.selected_projects
            resume_record.selected_skills = tailored_content.selected_skills
            resume_record.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(resume_record)

        # Log agent execution
        log = AgentExecutionLog(
            agent_name="ResumeGenerationAgent",
            execution_id=execution_id,
            task_type="TailoredResumeGeneration",
            status="SUCCESS",
            items_processed=1,
            items_failed=0,
            metadata_json={
                "candidate_id": candidate.id,
                "job_id": job.id,
                "coverage_score": coverage_report.coverage_percentage,
                "pdf_file": os.path.basename(pdf_path),
                "docx_file": os.path.basename(docx_path)
            },
            start_time=start_time,
            end_time=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

        return resume_record
