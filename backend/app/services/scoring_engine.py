from typing import Dict, Any, List, Tuple, Set, Optional
from backend.app.models import CandidateProfile, DiscoveredJob, UserPreferences
from backend.app.config import settings

# Semantic Skill Relationships (maps related skills to primary skills)
RELATED_SKILLS_MAP = {
    "spark": {"pyspark", "databricks", "hadoop"},
    "pyspark": {"spark", "databricks", "python"},
    "databricks": {"delta lake", "pyspark", "spark"},
    "delta lake": {"databricks", "pyspark", "spark"},
    "snowflake": {"sql", "cloud data warehouse", "dbt"},
    "dbt": {"snowflake", "sql", "data modeling", "etl", "elt"},
    "power bi": {"tableau", "bi & visualization", "reporting", "excel"},
    "tableau": {"power bi", "bi & visualization", "reporting"},
    "sql": {"postgresql", "mysql", "oracle", "snowflake", "sql server"},
    "postgresql": {"sql", "database developer"},
    "aws": {"s3", "glue", "redshift", "cloud"},
    "azure": {"adls", "synapse", "azure data factory", "cloud", "microsoft fabric"},
    "gcp": {"bigquery", "google cloud", "cloud"},
    "microsoft fabric": {"power bi", "azure", "delta lake", "synapse"},
    "lims": {"laboratory informatics", "clinical data management", "gxp"},
    "csv": {"computer system validation", "gxp", "21 cfr part 11", "data quality"},
    "gxp": {"csv", "computer system validation", "cdisc", "data governance"},
    "clinical data management": {"cdm", "sdtm", "cdisc", "pharmacovigilance"},
    "pharmacovigilance": {"drug safety", "clinical data management", "pv"},
}


class ScoringEngineService:
    """
    Intelligent Job Matching Engine implementing multi-factor deterministic and semantic scoring:
    - Technical skills match: 30%
    - Experience eligibility: 20%
    - Education eligibility: 15%
    - Job responsibilities & project match: 15%
    - Industry relevance: 10%
    - Location and employment preferences: 10%
    """

    @classmethod
    def evaluate_match(
        cls,
        candidate: CandidateProfile,
        job: DiscoveredJob,
        preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        rejection_reasons = []
        is_hard_eligible = True

        # 1. Technical Skills Match (30%)
        s_skills, matched_skills, partial_skills, missing_skills = cls._score_skills(candidate, job)

        # 2. Experience Eligibility (20%)
        s_exp, exp_mismatch = cls._score_experience(candidate, job)
        if exp_mismatch:
            is_hard_eligible = False
            rejection_reasons.append(exp_mismatch)

        # 3. Education Eligibility (15%)
        s_edu, edu_gap = cls._score_education(candidate, job)
        if edu_gap:
            rejection_reasons.append(edu_gap)

        # 4. Job Responsibilities & Projects Match (15%)
        s_resp = cls._score_responsibilities(candidate, job)

        # 5. Industry Relevance (10%)
        s_ind = cls._score_industry(candidate, job)

        # 6. Location & Employment Preferences (10%)
        s_loc = cls._score_location(candidate, job, preferences)

        # Overall weighted composite score (0 - 100)
        overall_score = (
            s_skills * settings.WEIGHT_TECHNICAL_SKILLS +
            s_exp * settings.WEIGHT_EXPERIENCE +
            s_edu * settings.WEIGHT_EDUCATION +
            s_resp * settings.WEIGHT_RESPONSIBILITIES +
            s_ind * settings.WEIGHT_INDUSTRY +
            s_loc * settings.WEIGHT_LOCATION_PREF
        )

        # Hard Eligibility Guard: Never misrepresent eligibility just to increase score
        if not is_hard_eligible:
            overall_score = min(overall_score, 55.0)

        overall_score = round(max(0.0, min(100.0, overall_score)), 1)

        # Categorical Label Assignment
        if overall_score >= 90.0:
            eligibility_label = "Excellent match"
        elif overall_score >= 80.0:
            eligibility_label = "Strong match"
        elif overall_score >= 70.0:
            eligibility_label = "Good match"
        elif overall_score >= 60.0:
            eligibility_label = "Partial match"
        else:
            eligibility_label = "Low match"

        # Actionable recommendation
        if overall_score >= 80.0 and is_hard_eligible:
            recommended_action = "Priority application: Generate tailored ATS resume and review for submission."
        elif overall_score >= 70.0:
            missing_names = [m["skill"] for m in missing_skills[:2]]
            rec = f"Good opportunity: Candidate meets primary technical requirements."
            if missing_names:
                rec += f" Note: Familiarize with {', '.join(missing_names)}."
            recommended_action = rec
        elif not is_hard_eligible:
            recommended_action = f"Caution: Hard eligibility barrier detected ({'; '.join(rejection_reasons)})."
        else:
            recommended_action = "Review requirements: Multiple core technical competencies missing."

        return {
            "overall_score": overall_score,
            "eligibility_label": eligibility_label,
            "is_hard_eligible": is_hard_eligible,
            "skills_score": s_skills,
            "experience_score": s_exp,
            "education_score": s_edu,
            "responsibility_score": s_resp,
            "industry_score": s_ind,
            "location_score": s_loc,
            "matched_skills": matched_skills,
            "partially_matched_skills": partial_skills,
            "missing_skills": missing_skills,
            "rejection_reasons": rejection_reasons,
            "recommended_action": recommended_action
        }

    @classmethod
    def _score_skills(
        cls,
        candidate: CandidateProfile,
        job: DiscoveredJob
    ) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Calculates skills score (0-100) and categorizes matched, partial, and missing skills."""
        candidate_skills = {s.name.lower(): s for s in candidate.skills}
        job_skills = job.skills

        if not job_skills:
            return 85.0, [], [], []

        matched = []
        partial = []
        missing = []
        points = 0.0
        max_possible = 0.0

        for js in job_skills:
            weight = 2.0 if js.is_mandatory else 1.0
            max_possible += weight
            j_skill_lower = js.skill_name.lower()

            # 1. Exact match
            if j_skill_lower in candidate_skills:
                points += weight
                matched.append({
                    "skill": js.skill_name,
                    "candidate_evidence": f"Verified proficiency: {candidate_skills[j_skill_lower].proficiency}",
                    "is_mandatory": js.is_mandatory
                })
                continue

            # 2. Semantic related skill match
            related_found = None
            for rel in RELATED_SKILLS_MAP.get(j_skill_lower, set()):
                if rel in candidate_skills:
                    related_found = candidate_skills[rel].name
                    break

            if related_found:
                points += weight * 0.75  # 75% credit for semantically related capability
                partial.append({
                    "skill": js.skill_name,
                    "related_skill": related_found,
                    "candidate_evidence": f"Related competency via {related_found}",
                    "is_mandatory": js.is_mandatory
                })
            else:
                missing.append({
                    "skill": js.skill_name,
                    "is_mandatory": js.is_mandatory
                })

        score = (points / max_possible * 100.0) if max_possible > 0 else 50.0
        return round(score, 1), matched, partial, missing

    @classmethod
    def _score_experience(cls, candidate: CandidateProfile, job: DiscoveredJob) -> Tuple[float, Optional[str]]:
        """Calculates experience score (0-100) and flags hard experience mismatches."""
        cand_exp = candidate.total_experience_years or 0.0
        job_min = job.min_experience or 0.0
        job_max = job.max_experience or (job_min + 3.0)

        # Fresher or within target early career window (0-2 years)
        if job_min <= 0.5:
            if cand_exp <= 2.0:
                return 100.0, None
            return 90.0, None

        # Candidate meets or exceeds minimum
        if cand_exp >= job_min:
            if cand_exp <= job_max:
                return 100.0, None
            return 85.0, None  # Slightly over-experienced

        # Candidate is below minimum requirement
        diff = job_min - cand_exp
        if diff >= 1.5:
            # Significant experience barrier (e.g. job requires 3+ yrs, candidate has 0-0.5)
            penalty_score = max(0.0, 40.0 - (diff * 10.0))
            mismatch_note = f"Experience mismatch: job requires minimum {job_min} years, candidate profile has {cand_exp} years."
            return round(penalty_score, 1), mismatch_note

        # Minor experience gap (e.g. requires 1 yr, candidate has 0.5 yr)
        return 75.0, None

    @classmethod
    def _score_education(cls, candidate: CandidateProfile, job: DiscoveredJob) -> Tuple[float, Optional[str]]:
        """Calculates education score (0-100) and detects qualification barriers."""
        if not candidate.education:
            return 60.0, None

        highest_edu = next((e for e in candidate.education if e.is_highest), candidate.education[0])
        degree = (highest_edu.degree or "").lower()
        field = (highest_edu.field_of_study or "").lower()
        job_req_text = ((job.education_requirements or "") + " " + (job.description or "")).lower()

        score = 80.0
        # Field of study match
        if any(f in field for f in ["computer science", "data science", "information technology", "biotechnology", "bioinformatics"]):
            score += 20.0
        elif any(f in field for f in ["electronics", "engineering", "statistics", "mathematics"]):
            score += 10.0

        # Degree qualification check
        if "ph.d" in job_req_text and "ph.d" not in degree:
            return 40.0, "Job requires Ph.D. qualification."

        return min(score, 100.0), None

    @classmethod
    def _score_responsibilities(cls, candidate: CandidateProfile, job: DiscoveredJob) -> float:
        """Evaluates project and technical portfolio alignment with vacancy responsibilities."""
        if not candidate.projects:
            return 60.0

        job_desc_lower = (job.description or "").lower()
        project_terms = []
        for p in candidate.projects:
            project_terms.extend([t.lower() for t in (p.technologies or [])])
            project_terms.extend((p.title or "").lower().split())

        overlap = sum(1 for term in set(project_terms) if term in job_desc_lower)
        if overlap >= 5:
            return 95.0
        elif overlap >= 3:
            return 85.0
        elif overlap >= 1:
            return 75.0
        return 65.0

    @classmethod
    def _score_industry(cls, candidate: CandidateProfile, job: DiscoveredJob) -> float:
        """Calculates industry category relevance (Pharma, Biotech, CRO, LifeSci Tech)."""
        job_cat = (job.category or "").lower()
        headline = (candidate.headline or "").lower()
        summary = (candidate.summary or "").lower()

        is_pharma_oriented = any(w in headline or w in summary for w in [
            "pharma", "clinical", "healthcare", "life sciences", "gxp", "biotech"
        ])

        if "clinical" in job_cat or "pharma" in job_cat:
            return 95.0 if is_pharma_oriented else 80.0
        return 90.0

    @classmethod
    def _score_location(
        cls,
        candidate: CandidateProfile,
        job: DiscoveredJob,
        preferences: Optional[UserPreferences] = None
    ) -> float:
        """Evaluates location proximity, relocation willingness, and remote work alignment."""
        job_city = (job.city or "India").lower()
        job_mode = (job.work_mode or "Hybrid").lower()
        cand_loc = (candidate.current_location or "India").lower()

        # Remote jobs are 100% accessible
        if "remote" in job_mode:
            return 100.0

        # Exact city match
        if cand_loc in job_city or job_city in cand_loc:
            return 100.0

        # Preferred locations configured by candidate
        if preferences and preferences.preferred_locations:
            pref_cities = [p.lower() for p in preferences.preferred_locations]
            if any(p in job_city or job_city in p for p in pref_cities):
                return 95.0

        # Candidate is willing to relocate
        if candidate.willing_to_relocate:
            return 85.0

        return 60.0
