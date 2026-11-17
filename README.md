# Pharma Job Hunter AI 🧬
### Autonomous Job Discovery, ATS Resume Optimization & Assisted Auto-Application Platform for Pharmaceutical & Life Sciences in India

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-39%20Passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Project Overview

**Pharma Job Hunter AI** is a production-grade autonomous agent platform designed to discover, extract, verify, match, ATS-optimize, and track data engineering and technical job applications across pharmaceutical, biotechnology, clinical research (CRO/CDMO), healthcare technology, and life sciences companies across **India**.

The system is built on an **11-Specialized-Agent Architecture** adhering to a strict **Assisted Application Mode** with zero hallucinations:
- **Truthful Candidate Representation:** Never invents candidate credentials, years of experience, or clinical trial certifications.
- **Assisted Application Gate:** Application packages and screening question answers are pre-mapped, but cannot be submitted without explicit candidate verification and approval.
- **Anti-Bot & CAPTCHA Compliance:** Respects `robots.txt`, career portal rate limits, and never bypasses authentication or CAPTCHAs.

---

## 2. Architecture & The 11 Autonomous Agents

```
                                  [ Candidate Profile & Resume ]
                                                │
                                    (5) Candidate Profile Agent
                                                │
[ 54+ Target Companies ] ── (1) Company Discovery ──► (2) Job Search Agent ◄── [ Multi-Source Portals ]
                                                │                   │
                                                ▼                   ▼
                                    (3) Job Extraction  ──► (4) Job Verification
                                                │
                                                ▼
                                    (6) Intelligent AI Matching
                                      (6-Factor Scoring Engine)
                                                │
                        ┌───────────────────────┴───────────────────────┐
                        ▼                                               ▼
          (7) ATS Optimization Agent                      (9) Application Automation
                        │                                               │
          (8) Dual Resume Generation (PDF/DOCX)           (10) Application Tracking
                        │                                               │
                        └───────────────────────┬───────────────────────┘
                                                ▼
                                   (11) Notification Agent
                                 (Dashboard / Email / Telegram)
```

| Agent | Name | Role & Responsibility |
|---|---|---|
| **Agent 1** | **Company Discovery Agent** | Discovers official career portals, ATS platforms (Workday, Greenhouse, Lever, Taleo), and maintains 54+ pharmaceutical companies in India. |
| **Agent 2** | **Job Search Agent** | Multi-source discovery across company career pages, APIs, RSS feeds, and authorized job sources. |
| **Agent 3** | **Job Extraction Agent** | Extracts structured requisition details into 7-pillar categories, location, experience bounds, and required skills. |
| **Agent 4** | **Job Verification Agent** | Audits application URLs to verify vacancies are `ACTIVE`. Flags closed or expired vacancies as `UNKNOWN` or `CLOSED`. |
| **Agent 5** | **Candidate Profile Agent** | Parses PDF/DOCX resumes, matches skills against taxonomy, and calculates profile readiness score. |
| **Agent 6** | **Job Matching Agent** | Calculates 6-factor score (0-100%) with hard eligibility guards (caps score at 55% for ineligible applicants). |
| **Agent 7** | **ATS Optimization Agent** | Analyzes keyword coverage, extracts job keywords, and optimizes summary/highlights without fabricating data. |
| **Agent 8** | **Resume Generation Agent** | Generates ATS-parseable single-column PDF (`reportlab`) and editable DOCX (`python-docx`) resumes. |
| **Agent 9** | **Application Automation Agent** | Maps candidate profile to form fields, answers screening questions truthfully, and halts at approval gate. |
| **Agent 10** | **Application Tracking Agent** | Prevents duplicate applications, audits 12 lifecycle stages, and maintains immutable event history. |
| **Agent 11** | **Notification Agent** | Dispatches dashboard, SMTP email, and Telegram alerts for high matches and interview invitations. |

---

## 3. Target Sectors & Geographic Coverage

### A. 5 Targeted Life Sciences Sectors in India
1. **Indian Pharmaceutical Giants (16 companies):** Dr. Reddy's Laboratories, Aurobindo Pharma, Sun Pharma, Cipla, Lupin, Zydus Lifesciences, Biocon, Torrent Pharma, Divi's Laboratories, Glenmark, Granules India, Laurus Labs, Mankind Pharma, Gland Pharma, Natco Pharma, Bharat Biotech.
2. **Global Pharma in India (15 companies):** Pfizer, Roche, Novartis, Sanofi, AstraZeneca, GSK, Eli Lilly, Merck, Bristol Myers Squibb, Amgen, Johnson & Johnson, AbbVie, Takeda, Novo Nordisk, Bayer.
3. **CRO & Clinical Research (8 companies):** IQVIA, Parexel, ICON, Syneos Health, Labcorp, Fortrea, Thermo Fisher Scientific, Charles River Laboratories.
4. **Biotechnology & CDMO (7 companies):** Biocon Biologics, Serum Institute of India, Bharat Biotech, Syngene International, MedGenome, Strand Life Sciences, Eurofins.
5. **Pharma Tech & Software (8 companies):** AmpleLogic, Veeva Systems, Indegene, Accenture Life Sciences, Cognizant Healthcare, TCS Life Sciences, Wipro Healthcare, Capgemini Life Sciences.

### B. Geographic Hubs
- **Priority Cities:** Hyderabad, Bengaluru, Chennai, Pune, Mumbai, Navi Mumbai, Ahmedabad, Noida, Gurugram, Delhi, Kolkata, Visakhapatnam, Chandigarh, Kochi, and Remote India.
- **Work Modes:** Work from Office, Hybrid, Remote (Full-time, Trainee, Internship).

---

## 4. 7-Pillar Technical Job Classification Taxonomy

Every vacancy is automatically classified into one of the following technical data categories:
1. **Data Engineering:** Data Engineer, ETL Developer, Azure/AWS Data Engineer, Databricks, Snowflake, PySpark, dbt Developer.
2. **Data Analytics:** Data Analyst, Healthcare Data Analyst, Clinical Data Analyst, Power BI, Tableau Developer.
3. **AI and Machine Learning:** AI Engineer, Machine Learning Engineer, NLP Engineer, Generative AI / RAG Developer.
4. **Database and SQL:** SQL Developer, Database Administrator, Data Warehouse Developer.
5. **Clinical & Pharmaceutical Data:** Clinical Data Programmer, CDISC/SDTM, LIMS Developer, Drug Safety Data Analyst.
6. **Pharma IT & Data Quality:** CSV Engineer (Computer System Validation), Data Governance Analyst, Data Steward.
7. **Other Technical:** Python Developer, Healthcare Interoperability, REST API Integration Developer.

---

## 5. Intelligent 6-Factor AI Matching Engine

Matching scores are calculated deterministically from 0 to 100%:

$$\text{Overall Score} = 0.30 \cdot S_{\text{tech}} + 0.20 \cdot S_{\text{exp}} + 0.15 \cdot S_{\text{edu}} + 0.15 \cdot S_{\text{resp}} + 0.10 \cdot S_{\text{ind}} + 0.10 \cdot S_{\text{loc}}$$

- **Technical Skills Match (30%):** Exact and semantic mapping (e.g. `PySpark` $\leftrightarrow$ `Spark`).
- **Experience Eligibility (20%):** Evaluated against candidate experience.
- **Education Eligibility (15%):** Degree and field of study match.
- **Job Responsibilities Match (15%):** Similarity to project portfolio.
- **Industry Relevance (10%):** Pharma, Biotech, and HealthTech alignment.
- **Location & Work Mode (10%):** City preferences and relocation willingness.

> **Hard Eligibility Guard:** If a vacancy strictly requires senior experience (e.g. 4+ years) and the candidate has 0–1 year, the overall score is strictly capped at **55.0%** to prevent false recommendations.

---

## 6. Quick Start & Installation

### Option 1: Local Development (Python 3.12 + SQLite)

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd "Pharma Agent"
   ```

2. **Create and activate Python virtual environment:**
   ```bash
   # Using uv (recommended) or standard venv
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate # Linux/macOS
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database schema & seed target pharma data:**
   ```bash
   python scripts/init_db.py
   python scripts/seed_data.py
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```

6. **Open the platform:**
   - **Interactive Web Dashboard:** `http://127.0.0.1:8000/dashboard`
   - **Interactive API Swagger Docs:** `http://127.0.0.1:8000/docs`
   - **System Health Check:** `http://127.0.0.1:8000/health`

---

### Option 2: Production Containerization (Docker Compose)

Run the full stack with PostgreSQL 16, Redis 7, Backend, and NGINX Frontend:

```bash
docker-compose up --build -d
```

- **Frontend Application:** `http://localhost:3000`
- **Backend API Gateway:** `http://localhost:8000`
- **PostgreSQL Database:** `localhost:5432`

---

## 7. Running the Automated Test Suite

The test suite contains 39 verified unit and integration tests covering all 11 agents and API layers:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -v
```

```
============================= test session starts =============================
collected 39 items

backend/tests/test_api.py::test_health_endpoint PASSED                   [  2%]
backend/tests/test_api.py::test_root_endpoint PASSED                     [  5%]
backend/tests/test_api.py::test_dashboard_endpoint PASSED                [  7%]
backend/tests/test_applications.py::test_form_mapper_service_fields_and_screening PASSED [ 10%]
backend/tests/test_applications.py::test_application_automation_prepare_and_preview PASSED [ 12%]
backend/tests/test_applications.py::test_submission_strictly_enforces_candidate_approval PASSED [ 15%]
backend/tests/test_applications.py::test_approval_and_submission_workflow PASSED [ 17%]
backend/tests/test_applications.py::test_duplicate_application_prevention PASSED [ 20%]
backend/tests/test_applications.py::test_application_tracking_lifecycle_and_milestones PASSED [ 23%]
backend/tests/test_applications.py::test_applications_api_route_functions PASSED [ 25%]
backend/tests/test_candidate.py::test_resume_parser_service_pdf PASSED   [ 28%]
backend/tests/test_candidate.py::test_resume_parser_service_docx PASSED  [ 30%]
backend/tests/test_candidate.py::test_candidate_profile_agent PASSED     [ 33%]
backend/tests/test_candidate.py::test_candidate_api_route_functions PASSED [ 35%]
backend/tests/test_candidate.py::test_upload_resume_route_function PASSED [ 38%]
backend/tests/test_companies.py::test_ats_adapters_detection PASSED      [ 41%]
backend/tests/test_companies.py::test_career_discovery_service PASSED    [ 43%]
backend/tests/test_companies.py::test_company_discovery_agent PASSED     [ 46%]
backend/tests/test_companies.py::test_companies_api_route_functions PASSED [ 48%]
backend/tests/test_jobs.py::test_job_extractor_service_classification PASSED [ 51%]
backend/tests/test_jobs.py::test_job_extractor_location_and_experience PASSED [ 53%]
backend/tests/test_jobs.py::test_job_extraction_agent PASSED             [ 56%]
backend/tests/test_jobs.py::test_job_verification_agent PASSED           [ 58%]
backend/tests/test_jobs.py::test_job_search_agent_and_api PASSED         [ 61%]
backend/tests/test_matching.py::test_scoring_engine_semantic_and_breakdown PASSED [ 64%]
backend/tests/test_matching.py::test_scoring_engine_hard_experience_mismatch PASSED [ 66%]
backend/tests/test_matching.py::test_job_matching_agent_and_notifications PASSED [ 69%]
backend/tests/test_matching.py::test_matching_api_route_functions PASSED [ 71%]
backend/tests/test_models.py::test_user_and_preferences PASSED           [ 74%]
backend/tests/test_models.py::test_candidate_profile_and_relations PASSED [ 76%]
backend/tests/test_models.py::test_company_and_job_deduplication PASSED  [ 79%]
backend/tests/test_models.py::test_matching_and_application_lifecycle PASSED [ 82%]
backend/tests/test_models.py::test_agent_execution_logs_and_notifications PASSED [ 84%]
backend/tests/test_notifications_scheduler.py::test_notification_agent_dispatch_and_milestones PASSED [ 87%]
backend/tests/test_notifications_scheduler.py::test_notifications_api_endpoints PASSED [ 89%]
backend/tests/test_notifications_scheduler.py::test_scheduler_status_and_lifecycle PASSED [ 92%]
backend/tests/test_resumes.py::test_resume_builder_service_pdf_and_docx PASSED [ 94%]
backend/tests/test_resumes.py::test_ats_optimization_agent PASSED        [ 97%]
backend/tests/test_resume_generation_agent_and_api PASSED [100%]

====================== 39 passed in 6.79s =======================
```

---

## 8. API Gateway Reference

| Group | Method | Endpoint | Description |
|---|---|---|---|
| **System** | `GET` | `/health` | Database, environment, and connectivity check |
| **UI** | `GET` | `/dashboard` | Interactive Web Dashboard SPA |
| **Candidate** | `GET` | `/api/v1/candidate/profile` | Verified profile snapshot |
| **Candidate** | `POST` | `/api/v1/candidate/upload-resume` | PDF/DOCX resume upload & parser |
| **Candidate** | `POST` | `/api/v1/candidate/profile/verify` | Candidate profile verification |
| **Companies** | `GET` | `/api/v1/companies` | List 54+ pharmaceutical companies |
| **Companies** | `POST` | `/api/v1/companies/discover` | Trigger dynamic company expansion |
| **Jobs** | `GET` | `/api/v1/jobs` | Filter jobs by category, city, experience |
| **Jobs** | `POST` | `/api/v1/jobs/discover` | Trigger multi-source job search cycle |
| **Matching** | `GET` | `/api/v1/matching/recommendations` | Top 6-factor scored opportunities |
| **Matching** | `POST` | `/api/v1/matching/evaluate-batch` | Re-score all vacancies for candidate |
| **Resumes** | `POST` | `/api/v1/resumes/generate` | Generate tailored ATS PDF & DOCX |
| **Resumes** | `GET` | `/api/v1/resumes/{id}/download` | Download optimized PDF / DOCX |
| **Applications** | `POST` | `/api/v1/applications/prepare` | Map form fields & screening answers |
| **Applications** | `GET` | `/api/v1/applications/{id}/preview` | Inspection snapshot before approval |
| **Applications** | `POST` | `/api/v1/applications/{id}/approve` | **Candidate explicit approval gate** |
| **Applications** | `POST` | `/api/v1/applications/{id}/submit` | Execute assisted submission |
| **Applications** | `GET` | `/api/v1/applications/stats` | Pipeline metrics by lifecycle state |
| **Notifications** | `GET` | `/api/v1/notifications` | Candidate in-app alerts |
| **Scheduler** | `GET` | `/api/v1/scheduler/status` | Autonomous agent cron schedules |
| **Scheduler** | `POST` | `/api/v1/scheduler/trigger/{task}` | Run scheduled cycle immediately |

---

## 9. Compliance & Ethical Boundaries

1. **Truthful Representation:** The resume generator and application auto-filler utilize **only** candidate-verified information. No fake experience, certifications, or pharma trials are ever synthesized.
2. **Assisted Application Priority:** Automated submission is strictly halted until the candidate reviews the mapped snapshot and provides explicit consent.
3. **Respect for Career Portals:** Adheres to `robots.txt`, respects portal rate limits, and uses official APIs and RSS feeds wherever available.
4. **No CAPTCHA / Anti-Bot Bypassing:** When a portal requires MFA or visual CAPTCHA, the agent prepares the pre-filled package and hands over directly to the user.

