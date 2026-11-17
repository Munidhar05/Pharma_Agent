from typing import Dict, Any, List
from backend.app.models.candidate import CandidateProfile


class CandidateProfileAgent:
    """
    Agent 5: Candidate Profile Agent
    Analyzes, structures, and validates the candidate's profile, calculating completeness
    and providing recommendations for maximum pharmaceutical job alignment.
    """

    def __init__(self, profile: CandidateProfile):
        self.profile = profile

    def analyze_profile(self) -> Dict[str, Any]:
        """Analyze completeness, identify gaps, and calculate profile readiness score."""
        score = 0
        checks = {}
        missing_items = []
        recommendations = []

        # 1. Contact Information (15 pts)
        has_phone = bool(self.profile.phone)
        has_linkedin = bool(self.profile.linkedin_url)
        has_github = bool(self.profile.github_url)
        contact_score = (5 if has_phone else 0) + (5 if has_linkedin else 0) + (5 if has_github else 0)
        score += contact_score
        checks["contact_info"] = {"score": contact_score, "max": 15}
        if not has_phone:
            missing_items.append("Phone number")
        if not has_linkedin:
            missing_items.append("LinkedIn profile URL")

        # 2. Education (20 pts)
        education_count = len(self.profile.education)
        edu_score = 20 if education_count > 0 else 0
        score += edu_score
        checks["education"] = {"score": edu_score, "max": 20, "count": education_count}
        if education_count == 0:
            missing_items.append("Educational qualifications")

        # 3. Technical Skills (25 pts)
        skill_count = len(self.profile.skills)
        if skill_count >= 8:
            skill_score = 25
        elif skill_count >= 4:
            skill_score = 15
        elif skill_count >= 1:
            skill_score = 10
        else:
            skill_score = 0
        score += skill_score
        checks["skills"] = {"score": skill_score, "max": 25, "count": skill_count}
        if skill_count < 5:
            recommendations.append("Add more technical skills relevant to data engineering and analytics (e.g., Python, SQL, Snowflake).")

        # 4. Project Experience (25 pts)
        project_count = len(self.profile.projects)
        if project_count >= 3:
            proj_score = 25
        elif project_count >= 1:
            proj_score = 15
        else:
            proj_score = 0
        score += proj_score
        checks["projects"] = {"score": proj_score, "max": 25, "count": project_count}
        if project_count == 0:
            missing_items.append("Technical projects or case studies")
            recommendations.append("Highlight projects involving ETL/ELT pipelines, data warehousing, or analytics.")

        # 5. Candidate Verification (15 pts)
        verified_score = 15 if self.profile.verified_by_candidate else 0
        score += verified_score
        checks["verification"] = {"score": verified_score, "max": 15, "verified": self.profile.verified_by_candidate}
        if not self.profile.verified_by_candidate:
            missing_items.append("Explicit candidate verification")
            recommendations.append("Review and verify your extracted profile to enable automated job application assistance.")

        # Domain Readiness Assessment
        pharma_relevant_skills = [
            s.name for s in self.profile.skills 
            if s.name.lower() in [
                "python", "sql", "pyspark", "snowflake", "databricks", "dbt", 
                "power bi", "tableau", "lims", "gxp", "csv", "cdisc", "etl"
            ]
        ]

        return {
            "profile_id": self.profile.id,
            "completeness_score": min(score, 100),
            "is_verified": self.profile.verified_by_candidate,
            "checks": checks,
            "missing_items": missing_items,
            "recommendations": recommendations,
            "pharma_relevant_skills": pharma_relevant_skills,
            "status": "Ready for Discovery" if score >= 75 and self.profile.verified_by_candidate else "Action Required"
        }

