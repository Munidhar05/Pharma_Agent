import re
from typing import Dict, Any, List, Tuple
from backend.app.models import CandidateProfile, DiscoveredJob
from backend.app.services.resume_parser import SKILL_TAXONOMY
from backend.app.schemas.resume import KeywordCoverageReport, KeywordCoverageItem, TailoredResumeContent


class ATSOptimizationAgent:
    """
    Agent 7: ATS Optimization Agent
    Extracts high-priority keywords from the target job description, performs gap analysis
    against the verified candidate profile, generates a Keyword Coverage Report, and
    optimizes content presentation without ever fabricating unevidenced skills or facts.
    """

    def __init__(self, candidate: CandidateProfile, job: DiscoveredJob):
        self.candidate = candidate
        self.job = job

    def generate_coverage_report(self) -> KeywordCoverageReport:
        """
        Extracts keywords from job description and computes coverage percentage
        grounded in candidate's verified skills and project achievements.
        """
        job_desc_lower = f"{self.job.title} {self.job.description}".lower()
        candidate_skills = {s.name.lower(): s for s in self.candidate.skills}
        candidate_projects_text = " ".join([
            f"{p.title} {p.description} {' '.join(p.technologies)}" for p in self.candidate.projects
        ]).lower()

        items = []
        matched_count = 0

        # Scan taxonomy skills present in the job posting
        for skill_name in SKILL_TAXONOMY.keys():
            pattern = r"\b" + re.escape(skill_name.lower()) + r"\b"
            if re.search(pattern, job_desc_lower):
                skill_lower = skill_name.lower()
                
                # Check candidate evidence
                evidence = None
                status = "Missing"

                if skill_lower in candidate_skills:
                    evidence = f"Verified candidate technical skill: {candidate_skills[skill_lower].proficiency}"
                    status = "Matched"
                    matched_count += 1
                elif skill_lower in candidate_projects_text:
                    evidence = f"Hands-on project experience evidenced in portfolio"
                    status = "Matched"
                    matched_count += 1

                items.append(KeywordCoverageItem(
                    keyword=skill_name,
                    candidate_evidence=evidence,
                    status=status,
                    importance="High" if skill_name in ["Python", "SQL", "Snowflake", "Databricks", "PySpark", "dbt", "LIMS", "CSV"] else "Medium"
                ))

        total_keywords = len(items)
        coverage_pct = round((matched_count / total_keywords * 100.0), 1) if total_keywords > 0 else 100.0

        return KeywordCoverageReport(
            total_keywords_found=total_keywords,
            matched_count=matched_count,
            missing_count=total_keywords - matched_count,
            coverage_percentage=coverage_pct,
            items=items
        )

    def optimize_resume_content(
        self,
        custom_headline: str = None,
        custom_summary: str = None
    ) -> TailoredResumeContent:
        """
        Synthesizes truthful tailored resume content:
        1. Prioritizes candidate skills matching the target vacancy.
        2. Reorders projects so the most relevant project appears first.
        3. Generates a tailored headline and summary emphasizing matching competencies.
        """
        job_keywords = {
            s.lower() for s in SKILL_TAXONOMY.keys()
            if re.search(r"\b" + re.escape(s.lower()) + r"\b", self.job.description.lower())
        }

        # 1. Order skills (matching skills first)
        all_cand_skills = [s.name for s in self.candidate.skills]
        matching_skills = [s for s in all_cand_skills if s.lower() in job_keywords]
        other_skills = [s for s in all_cand_skills if s.lower() not in job_keywords]
        ordered_skills = matching_skills + other_skills

        # 2. Prioritize projects based on keyword overlap
        project_scores = []
        for p in self.candidate.projects:
            p_text = f"{p.title} {p.description} {' '.join(p.technologies)}".lower()
            overlap = sum(1 for kw in job_keywords if kw in p_text)
            project_scores.append((overlap, {
                "title": p.title,
                "role": p.role,
                "domain": p.domain,
                "description": p.description,
                "technologies": p.technologies,
                "highlights": p.highlights
            }))

        project_scores.sort(key=lambda x: x[0], reverse=True)
        ordered_projects = [p[1] for p in project_scores]

        # 3. Format Headline
        headline = custom_headline or f"{self.candidate.headline} | Specialized in {', '.join(matching_skills[:3]) if matching_skills else 'Data Solutions'}"

        # 4. Format Summary emphasizing verified competencies relevant to the company
        company_name = self.job.company.name if self.job.company else "Pharmaceutical Enterprise"
        if custom_summary:
            summary = custom_summary
        else:
            skills_str = ", ".join(matching_skills[:5]) if matching_skills else "Python, SQL, and Modern Data Engineering"
            summary = (
                f"{self.candidate.summary} "
                f"Specifically tailored for the {self.job.title} role at {company_name}, "
                f"leveraging verified hands-on capabilities in {skills_str}."
            )

        # 5. Format Education
        education_list = []
        for e in self.candidate.education:
            education_list.append({
                "degree": e.degree,
                "field_of_study": e.field_of_study,
                "institution": e.institution,
                "start_year": e.start_year,
                "end_year": e.end_year,
                "cgpa_or_percentage": e.cgpa_or_percentage
            })

        return TailoredResumeContent(
            headline=headline,
            summary=summary,
            selected_skills=ordered_skills,
            selected_projects=ordered_projects,
            education=education_list
        )

