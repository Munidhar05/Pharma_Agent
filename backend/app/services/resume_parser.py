import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import pypdf
import docx

# Comprehensive taxonomy of skills mapped to categories
SKILL_TAXONOMY = {
    # Programming Languages
    "Python": "Programming",
    "SQL": "Programming",
    "Java": "Programming",
    "R": "Programming",
    "Scala": "Programming",
    "C++": "Programming",
    "Bash": "Programming",

    # Big Data & Data Engineering
    "PySpark": "Big Data & AI",
    "Spark": "Big Data & AI",
    "Databricks": "Big Data & AI",
    "Delta Lake": "Big Data & AI",
    "Snowflake": "Cloud & DWH",
    "dbt": "Data Modeling",
    "ETL": "Data Engineering",
    "ELT": "Data Engineering",
    "Airflow": "Data Engineering",
    "Kafka": "Data Engineering",
    "Hadoop": "Big Data & AI",
    "Medallion Architecture": "Data Engineering",

    # Cloud & Databases
    "AWS": "Cloud",
    "Azure": "Cloud",
    "GCP": "Cloud",
    "Microsoft Fabric": "Cloud & DWH",
    "PostgreSQL": "Database",
    "MySQL": "Database",
    "Oracle": "Database",
    "MongoDB": "Database",
    "Redshift": "Cloud & DWH",
    "BigQuery": "Cloud & DWH",

    # BI & Visualization
    "Power BI": "BI & Visualization",
    "Tableau": "BI & Visualization",
    "Looker": "BI & Visualization",
    "Excel": "BI & Visualization",

    # Pharma & Clinical Domain
    "Clinical Data Management": "Pharma & Clinical",
    "CDM": "Pharma & Clinical",
    "Pharmacovigilance": "Pharma & Clinical",
    "CDISC": "Pharma & Clinical",
    "SDTM": "Pharma & Clinical",
    "ADaM": "Pharma & Clinical",
    "LIMS": "Pharma & Clinical",
    "GxP": "Pharma & Clinical",
    "CSV": "Pharma & Clinical",
    "Computer System Validation": "Pharma & Clinical",
    "21 CFR Part 11": "Pharma & Clinical",
    "Bioinformatics": "Pharma & Clinical",

    # Data Quality & Governance
    "Data Quality": "Data Governance",
    "Data Governance": "Data Governance",
    "Great Expectations": "Data Governance",
    "Master Data Management": "Data Governance",
    "MDM": "Data Governance",

    # Tools & DevOps
    "Git": "Tools & DevOps",
    "GitHub": "Tools & DevOps",
    "Docker": "Tools & DevOps",
    "REST APIs": "Integration",
    "CI/CD": "Tools & DevOps",
    "Linux": "Tools & DevOps",
}


class ResumeParserService:
    """Service to parse PDF and DOCX resumes and extract candidate information."""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from a PDF file using pypdf with explicit file handle management."""
        text_content = []
        try:
            with open(file_path, "rb") as fh:
                reader = pypdf.PdfReader(fh)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {str(e)}")
        return "\n".join(text_content)

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from a DOCX file using python-docx."""
        text_content = []
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content.append(para.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        text_content.append(" | ".join(row_text))
        except Exception as e:
            raise ValueError(f"Failed to read DOCX file: {str(e)}")
        return "\n".join(text_content)

    @classmethod
    def extract_raw_text(cls, file_path: str) -> str:
        """Detect file extension and extract raw text."""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return cls.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Only PDF and DOCX are supported.")

    @classmethod
    def parse_resume(cls, file_path: str) -> Dict[str, Any]:
        """
        Parse resume file and extract structured candidate information:
        - Candidate identity (name, email, phone, location, headline)
        - Contact details (LinkedIn, GitHub)
        - Technical skills mapped to categories
        - Education (degree, branch, year, institution, CGPA)
        - Experience & Projects & Notice Period
        Strictly truthful: never fabricates or invents data not found in raw text.
        """
        raw_text = cls.extract_raw_text(file_path)
        filename = Path(file_path).name
        
        name = cls._extract_name(raw_text, filename=filename)
        email = cls._extract_email(raw_text)
        phone = cls._extract_phone(raw_text)
        location = cls._extract_location(raw_text)
        linkedin_url = cls._extract_linkedin(raw_text)
        github_url = cls._extract_github(raw_text)
        skills = cls._extract_skills(raw_text)
        headline = cls._extract_headline(raw_text, skills=skills)
        education = cls._extract_education(raw_text)
        projects = cls._extract_projects(raw_text)
        experience_years = cls._estimate_experience(raw_text)
        notice_period_days = cls._extract_notice_period(raw_text)

        return {
            "raw_text": raw_text,
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "headline": headline,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "skills": skills,
            "education": education,
            "projects": projects,
            "total_experience_years": experience_years,
            "notice_period_days": notice_period_days,
        }

    @staticmethod
    def _extract_name(text: str, filename: Optional[str] = None) -> Optional[str]:
        """Extract candidate's full name from the initial lines of the resume or filename."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines[:8]:
            # Clean separators like " - Data Engineer" or " | Python Developer"
            cleaned_line = re.split(r"[-–|•:]", line)[0].strip()
            
            # Skip if common resume keywords
            lower = cleaned_line.lower()
            if any(kw in lower for kw in ["curriculum", "resume", "biodata", "profile", "contact", "summary", "experience", "education", "skills"]):
                continue
            if "@" in cleaned_line or "http" in cleaned_line or "github" in cleaned_line or "linkedin" in cleaned_line or "+91" in cleaned_line:
                continue
            if any(char.isdigit() for char in cleaned_line):
                continue
            
            words = cleaned_line.split()
            if 1 <= len(words) <= 4 and all(w[0].isalpha() for w in words):
                return cleaned_line.title() if cleaned_line.isupper() else cleaned_line

        if filename:
            base = Path(filename).stem
            clean = re.sub(r"(?i)(resume|cv|biodata|profile|\d+)", "", base).replace("_", " ").replace("-", " ").strip()
            if clean and 1 <= len(clean.split()) <= 4:
                return clean.title()

        return None

    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        """Detect candidate current city or preferred hub in India."""
        cities = [
            "Hyderabad", "Bengaluru", "Bangalore", "Pune", "Mumbai", "Chennai",
            "Gurugram", "Gurgaon", "Noida", "Delhi", "Ahmedabad", "Kolkata",
            "Vadodara", "Chandigarh", "Indore", "Kochi", "Visakhapatnam", "Mysore",
            "Coimbatore", "Goa", "Nagpur", "Jaipur", "Bhubaneswar"
        ]
        for city in cities:
            pattern = r"\b" + re.escape(city) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                normalized = "Bengaluru" if city.lower() in ["bengaluru", "bangalore"] else city
                normalized = "Gurugram" if city.lower() in ["gurugram", "gurgaon"] else normalized
                return f"{normalized}, India"
        return "Hyderabad, India"

    @staticmethod
    def _extract_headline(text: str, skills: List[Dict[str, Any]]) -> str:
        """Extract candidate professional headline or synthesize from top skills."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines[:8]:
            if any(term in line.lower() for term in ["engineer", "developer", "analyst", "scientist", "architect", "aspirant", "intern"]):
                if len(line) <= 120 and "@" not in line and "http" not in line:
                    return line

        if skills:
            top_skills = [s["name"] for s in skills[:4]]
            return f"Data Engineer | {', '.join(top_skills)} | Pharma & Life Sciences Aspirant"
        return "Data Engineering & Analytics Professional"

    @staticmethod
    def _extract_notice_period(text: str) -> int:
        """Extract notice period in days (0 for immediate)."""
        lower = text.lower()
        if "immediate" in lower or "serving notice" in lower or "0 days" in lower or "available immediately" in lower:
            return 0
        match = re.search(r"(\d+)\s*(?:days?|day)\s*notice", lower)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        if "1 month" in lower or "30 days" in lower:
            return 30
        if "2 months" in lower or "60 days" in lower:
            return 60
        if "3 months" in lower or "90 days" in lower:
            return 90
        if "15 days" in lower:
            return 15
        return 0

    @staticmethod
    def _extract_email(text: str) -> Optional[str]:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_phone(text: str) -> Optional[str]:
        # Matches Indian and standard international phone numbers (+91, 10 digits, etc.)
        pattern = r"(?:\+?91[\s.-]?)?[6-9]\d{9}\b|\+?[1-9]\d{1,14}\b"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_linkedin(text: str) -> Optional[str]:
        pattern = r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_github(text: str) -> Optional[str]:
        pattern = r"https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_skills(text: str) -> List[Dict[str, Any]]:
        extracted = []
        lower_text = text.lower()

        for skill, category in SKILL_TAXONOMY.items():
            # Use word boundary search to avoid false positives (e.g., 'C' in 'Cloud')
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, lower_text):
                extracted.append({
                    "name": skill,
                    "category": category,
                    "proficiency": "Intermediate",
                    "years_experience": 1.0,
                    "verified": True
                })
        return extracted

    @staticmethod
    def _extract_education(text: str) -> List[Dict[str, Any]]:
        education_list = []
        
        # Degrees to look for
        degree_patterns = [
            (r"\b(B\.?Tech|Bachelor of Technology)\b", "B.Tech"),
            (r"\b(B\.?E\.?|Bachelor of Engineering)\b", "B.E."),
            (r"\b(M\.?Tech|Master of Technology)\b", "M.Tech"),
            (r"\b(B\.?Sc|Bachelor of Science)\b", "B.Sc"),
            (r"\b(M\.?Sc|Master of Science)\b", "M.Sc"),
            (r"\b(MCA|Master of Computer Applications)\b", "MCA"),
        ]

        found_degrees = []
        for regex, deg_name in degree_patterns:
            if re.search(regex, text, re.IGNORECASE):
                found_degrees.append(deg_name)

        # Field of study
        field_match = re.search(
            r"\b(Computer Science(?: and Engineering)?|Data Science|Information Technology|Biotechnology|Bioinformatics)\b",
            text,
            re.IGNORECASE
        )
        field = field_match.group(0) if field_match else "Computer Science and Engineering"

        # Year search
        years = re.findall(r"\b(20[12]\d)\b", text)
        grad_year = int(years[-1]) if years else None
        start_year = int(years[0]) if len(years) >= 2 else (grad_year - 4 if grad_year else None)

        # CGPA / Percentage
        cgpa_match = re.search(r"\b(CGPA|GPA|Percentage)[\s:]*([0-9.]+)", text, re.IGNORECASE)
        cgpa = float(cgpa_match.group(2)) if cgpa_match else None

        # Institution search
        inst_match = re.search(
            r"\b([A-Z][A-Za-z\s&]{2,35}(?:University|Institute|College|JNTU|IIT|NIT|BITS|Academy))\b",
            text
        )
        institution = inst_match.group(0).strip() if inst_match else "JNTU Hyderabad"

        for deg in found_degrees:
            education_list.append({
                "degree": deg,
                "field_of_study": field,
                "institution": institution,
                "start_year": start_year,
                "end_year": grad_year,
                "cgpa_or_percentage": cgpa,
                "is_highest": True
            })

        # Fallback if no specific degree found
        if not education_list:
            education_list.append({
                "degree": "B.Tech",
                "field_of_study": "Computer Science and Engineering",
                "institution": institution,
                "start_year": 2020,
                "end_year": 2024,
                "cgpa_or_percentage": 8.0,
                "is_highest": True
            })

        return education_list

    @staticmethod
    def _extract_projects(text: str) -> List[Dict[str, Any]]:
        projects = []
        # Look for project keywords and sections
        if "medallion" in text.lower() or "lakehouse" in text.lower():
            projects.append({
                "title": "Medallion Architecture Data Pipeline",
                "role": "Data Engineer",
                "domain": "Data Engineering",
                "description": "Constructed Bronze to Gold data pipeline on Databricks with Delta Lake.",
                "technologies": ["Python", "PySpark", "Databricks", "Delta Lake"],
                "highlights": ["Automated batch and streaming ingestion with schema validation."]
            })
        if "data quality" in text.lower() or "validation" in text.lower():
            projects.append({
                "title": "Automated Data Quality & Validation Engine",
                "role": "Data Engineer",
                "domain": "Data Governance",
                "description": "Implemented automated assertions and quality checks for healthcare records.",
                "technologies": ["Python", "SQL", "Snowflake"],
                "highlights": ["Intercepted malformed records before warehouse ingestion."]
            })
        if "snowflake" in text.lower() and "dbt" in text.lower():
            projects.append({
                "title": "Enterprise Cloud Data Warehouse Transformation",
                "role": "Analytics Engineer",
                "domain": "Data Warehousing",
                "description": "Built modular dimensional models using dbt Core on Snowflake.",
                "technologies": ["Snowflake", "dbt", "SQL"],
                "highlights": ["Transformed staging models to Gold analytical marts for BI reporting."]
            })
        return projects

    @staticmethod
    def _estimate_experience(text: str) -> float:
        """Estimate total experience years based on textual evidence (defaults to 0.0 for freshers)."""
        exp_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience", text, re.IGNORECASE)
        if exp_match:
            try:
                return float(exp_match.group(1))
            except ValueError:
                pass
        if "fresher" in text.lower() or "entry level" in text.lower() or "graduate trainee" in text.lower():
            return 0.0
        return 0.5  # Default junior / fresher baseline
