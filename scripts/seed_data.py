import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import SessionLocal, init_db
from backend.app.models import (
    User,
    UserPreferences,
    CandidateProfile,
    CandidateSkill,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    Company,
    CompanyCareerSource,
    JobSource,
    Notification
)

# Initial seed data for companies across all 5 sectors specified in Section 3
TARGET_COMPANIES = [
    # A. Pharmaceutical Companies in India
    {"name": "Dr. Reddy's Laboratories", "slug": "dr-reddys", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://careers.drreddys.com"},
    {"name": "Aurobindo Pharma", "slug": "aurobindo", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://www.aurobindo.com/careers"},
    {"name": "Sun Pharmaceutical Industries", "slug": "sun-pharma", "industry": "Indian Pharma", "hq": "Mumbai", "careers": "https://sunpharma.com/careers"},
    {"name": "Cipla", "slug": "cipla", "industry": "Indian Pharma", "hq": "Mumbai", "careers": "https://www.cipla.com/careers"},
    {"name": "Lupin", "slug": "lupin", "industry": "Indian Pharma", "hq": "Mumbai", "careers": "https://www.lupin.com/careers"},
    {"name": "Zydus Lifesciences", "slug": "zydus", "industry": "Indian Pharma", "hq": "Ahmedabad", "careers": "https://www.zyduslife.com/careers"},
    {"name": "Biocon", "slug": "biocon", "industry": "Indian Pharma", "hq": "Bengaluru", "careers": "https://www.biocon.com/careers"},
    {"name": "Torrent Pharmaceuticals", "slug": "torrent-pharma", "industry": "Indian Pharma", "hq": "Ahmedabad", "careers": "https://www.torrentpharma.com/careers"},
    {"name": "Divi's Laboratories", "slug": "divis-lab", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://divislabs.com/careers"},
    {"name": "Glenmark Pharmaceuticals", "slug": "glenmark", "industry": "Indian Pharma", "hq": "Mumbai", "careers": "https://www.glenmarkpharma.com/careers"},
    {"name": "Granules India", "slug": "granules", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://granulesindia.com/careers"},
    {"name": "Laurus Labs", "slug": "laurus-labs", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://www.lauruslabs.com/careers"},
    {"name": "Mankind Pharma", "slug": "mankind", "industry": "Indian Pharma", "hq": "Delhi NCR", "careers": "https://www.mankindpharma.com/careers"},
    {"name": "Gland Pharma", "slug": "gland-pharma", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://www.glandpharma.com/careers"},
    {"name": "Natco Pharma", "slug": "natco-pharma", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://natcopharma.co.in/careers"},
    {"name": "Bharat Biotech", "slug": "bharat-biotech", "industry": "Indian Pharma", "hq": "Hyderabad", "careers": "https://www.bharatbiotech.com/careers"},

    # B. Global Pharmaceutical Companies in India
    {"name": "Pfizer", "slug": "pfizer", "industry": "Global Pharma", "hq": "Mumbai / Chennai", "careers": "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"},
    {"name": "Roche", "slug": "roche", "industry": "Global Pharma", "hq": "Hyderabad / Mumbai", "careers": "https://roche.wd3.myworkdayjobs.com/roche-ext"},
    {"name": "Novartis", "slug": "novartis", "industry": "Global Pharma", "hq": "Hyderabad", "careers": "https://www.novartis.com/careers"},
    {"name": "Sanofi", "slug": "sanofi", "industry": "Global Pharma", "hq": "Hyderabad / Mumbai", "careers": "https://sanofi.wd3.myworkdayjobs.com/SanofiCareers"},
    {"name": "AstraZeneca", "slug": "astrazeneca", "industry": "Global Pharma", "hq": "Bengaluru / Chennai", "careers": "https://careers.astrazeneca.com"},
    {"name": "GSK", "slug": "gsk", "industry": "Global Pharma", "hq": "Bengaluru / Mumbai", "careers": "https://gsk.wd5.myworkdayjobs.com/GSKCareers"},
    {"name": "Eli Lilly", "slug": "eli-lilly", "industry": "Global Pharma", "hq": "Bengaluru / Gurugram", "careers": "https://jobsearch.lilly.com"},
    {"name": "Merck", "slug": "merck", "industry": "Global Pharma", "hq": "Bengaluru / Mumbai", "careers": "https://jobs.merck.com"},
    {"name": "Bristol Myers Squibb", "slug": "bms", "industry": "Global Pharma", "hq": "Hyderabad", "careers": "https://bms.wd5.myworkdayjobs.com/BMS"},
    {"name": "Amgen", "slug": "amgen", "industry": "Global Pharma", "hq": "Hyderabad", "careers": "https://amgen.wd1.myworkdayjobs.com/Careers"},
    {"name": "Johnson & Johnson", "slug": "jnj", "industry": "Global Pharma", "hq": "Mumbai / Bengaluru", "careers": "https://jobs.jnj.com"},
    {"name": "AbbVie", "slug": "abbvie", "industry": "Global Pharma", "hq": "Bengaluru", "careers": "https://abbvie.wd1.myworkdayjobs.com/AbbVieCareers"},
    {"name": "Takeda", "slug": "takeda", "industry": "Global Pharma", "hq": "Gurugram", "careers": "https://takeda.wd3.myworkdayjobs.com/External"},
    {"name": "Novo Nordisk", "slug": "novo-nordisk", "industry": "Global Pharma", "hq": "Bengaluru", "careers": "https://www.novonordisk.com/careers"},
    {"name": "Bayer", "slug": "bayer", "industry": "Global Pharma", "hq": "Thane / Hyderabad", "careers": "https://career.bayer.com"},

    # C. CRO and Clinical Research Companies
    {"name": "IQVIA", "slug": "iqvia", "industry": "CRO & Clinical Research", "hq": "Bengaluru / Kochi / Thane", "careers": "https://jobs.iqvia.com"},
    {"name": "Parexel", "slug": "parexel", "industry": "CRO & Clinical Research", "hq": "Hyderabad / Bengaluru / Mohali", "careers": "https://jobs.parexel.com"},
    {"name": "ICON plc", "slug": "icon", "industry": "CRO & Clinical Research", "hq": "Chennai / Bengaluru / Trivandrum", "careers": "https://careers.iconplc.com"},
    {"name": "Syneos Health", "slug": "syneos-health", "industry": "CRO & Clinical Research", "hq": "Hyderabad / Gurugram / Pune", "careers": "https://syneoshealth.com/careers"},
    {"name": "Labcorp", "slug": "labcorp", "industry": "CRO & Clinical Research", "hq": "Bengaluru", "careers": "https://careers.labcorp.com"},
    {"name": "Fortrea", "slug": "fortrea", "industry": "CRO & Clinical Research", "hq": "Bengaluru / Pune", "careers": "https://careers.fortrea.com"},
    {"name": "Thermo Fisher Scientific", "slug": "thermo-fisher", "industry": "CRO & Clinical Research", "hq": "Bengaluru / Hyderabad", "careers": "https://jobs.thermofisher.com"},
    {"name": "Charles River Laboratories", "slug": "charles-river", "industry": "CRO & Clinical Research", "hq": "Bengaluru", "careers": "https://jobs.criver.com"},

    # D. Biotechnology and Life Sciences Companies
    {"name": "Biocon Biologics", "slug": "biocon-biologics", "industry": "Biotech & Life Sciences", "hq": "Bengaluru", "careers": "https://www.bioconbiologics.com/careers"},
    {"name": "Serum Institute of India", "slug": "serum-institute", "industry": "Biotech & Life Sciences", "hq": "Pune", "careers": "https://www.seruminstitute.com/careers"},
    {"name": "Syngene International", "slug": "syngene", "industry": "Biotech & Life Sciences", "hq": "Bengaluru / Hyderabad", "careers": "https://www.syngeneintl.com/careers"},
    {"name": "MedGenome", "slug": "medgenome", "industry": "Biotech & Life Sciences", "hq": "Bengaluru", "careers": "https://www.medgenome.com/careers"},
    {"name": "Strand Life Sciences", "slug": "strand-life-sciences", "industry": "Biotech & Life Sciences", "hq": "Bengaluru", "careers": "https://strandls.com/careers"},
    {"name": "Eurofins", "slug": "eurofins", "industry": "Biotech & Life Sciences", "hq": "Bengaluru / Hyderabad", "careers": "https://careers.eurofins.com"},
    {"name": "Genpact Life Sciences", "slug": "genpact-lifesciences", "industry": "Biotech & Life Sciences", "hq": "Hyderabad / Noida", "careers": "https://www.genpact.com/careers"},

    # E. Pharma Technology and Software Companies
    {"name": "AmpleLogic", "slug": "amplelogic", "industry": "Pharma Tech", "hq": "Hyderabad", "careers": "https://www.amplelogic.com/careers"},
    {"name": "Veeva Systems", "slug": "veeva-systems", "industry": "Pharma Tech", "hq": "Hyderabad / Bengaluru", "careers": "https://careers.veeva.com"},
    {"name": "Indegene", "slug": "indegene", "industry": "Pharma Tech", "hq": "Bengaluru", "careers": "https://www.indegene.com/careers"},
    {"name": "Accenture Life Sciences", "slug": "accenture-lifesciences", "industry": "Pharma Tech", "hq": "Bengaluru / Hyderabad", "careers": "https://www.accenture.com/in-en/careers"},
    {"name": "Cognizant Healthcare", "slug": "cognizant-healthcare", "industry": "Pharma Tech", "hq": "Hyderabad / Chennai / Pune", "careers": "https://careers.cognizant.com"},
    {"name": "TCS Life Sciences", "slug": "tcs-lifesciences", "industry": "Pharma Tech", "hq": "Hyderabad / Mumbai / Chennai", "careers": "https://www.tcs.com/careers"},
    {"name": "Wipro Healthcare", "slug": "wipro-healthcare", "industry": "Pharma Tech", "hq": "Bengaluru / Hyderabad", "careers": "https://careers.wipro.com"},
    {"name": "Capgemini Life Sciences", "slug": "capgemini-lifesciences", "industry": "Pharma Tech", "hq": "Pune / Bengaluru / Hyderabad", "careers": "https://www.capgemini.com/in-en/careers"},
]

JOB_SOURCES = [
    {"name": "Official ATS", "source_type": "direct_ats", "base_url": "https://careers.company.com", "rate_limit": 60},
    {"name": "LinkedIn Jobs", "source_type": "portal_api", "base_url": "https://www.linkedin.com/jobs", "rate_limit": 30},
    {"name": "Naukri", "source_type": "portal_api", "base_url": "https://www.naukri.com", "rate_limit": 30},
    {"name": "Indeed India", "source_type": "portal_api", "base_url": "https://in.indeed.com", "rate_limit": 30},
    {"name": "Foundit India", "source_type": "portal_api", "base_url": "https://www.foundit.in", "rate_limit": 30},
    {"name": "Instahyre", "source_type": "portal_api", "base_url": "https://www.instahyre.com", "rate_limit": 30},
    {"name": "Public Career Feeds", "source_type": "rss_feed", "base_url": "https://careers-feed.internal", "rate_limit": 120},
]


def seed_database():
    init_db()
    db = SessionLocal()

    try:
        print("1. Checking & Seeding Job Sources...")
        for src in JOB_SOURCES:
            existing = db.query(JobSource).filter(JobSource.name == src["name"]).first()
            if not existing:
                db.add(JobSource(
                    name=src["name"],
                    source_type=src["source_type"],
                    base_url=src["base_url"],
                    rate_limit_per_min=src["rate_limit"],
                    is_active=True
                ))
        db.commit()

        print("2. Checking & Seeding Companies & Career Sources...")
        for comp_data in TARGET_COMPANIES:
            comp = db.query(Company).filter(Company.slug == comp_data["slug"]).first()
            if not comp:
                comp = Company(
                    name=comp_data["name"],
                    slug=comp_data["slug"],
                    industry_category=comp_data["industry"],
                    hq_location=comp_data["hq"],
                    careers_url=comp_data["careers"],
                    is_active=True
                )
                db.add(comp)
                db.flush()

                # Add default career source
                source_type = "Workday" if "myworkdayjobs" in comp_data["careers"] else "Direct"
                db.add(CompanyCareerSource(
                    company_id=comp.id,
                    source_type=source_type,
                    base_url=comp_data["careers"],
                    career_url=comp_data["careers"],
                    is_active=True
                ))
        db.commit()
        print(f"   Successfully verified {len(TARGET_COMPANIES)} pharmaceutical & life science companies.")

        print("3. Checking & Seeding Demo Candidate Profile (from Section 8 requirements)...")
        demo_user = db.query(User).filter(User.email == "kandulamunidharreddy@gmail.com").first()
        if not demo_user:
            demo_user = User(
                email="kandulamunidharreddy@gmail.com",
                password_hash="$2b$12$eDxU1e7Q3wY4e5rT6y7u8OPasswordHashPlaceholderForDemo",
                full_name="Munidhar Kandula",
                role="candidate",
                is_active=True
            )
            db.add(demo_user)
            db.flush()

            # User Preferences
            prefs = UserPreferences(
                user_id=demo_user.id,
                preferred_locations=["Hyderabad", "Bengaluru", "Pune", "Remote India"],
                preferred_domains=["Data Engineering", "Data Analytics", "Clinical Data", "Pharma IT"],
                min_match_score_alert=70,
                auto_prepare_resumes=True,
                notification_channels=["dashboard"]
            )
            db.add(prefs)

            # Candidate Profile
            profile = CandidateProfile(
                user_id=demo_user.id,
                headline="Junior Data Engineer | Snowflake, Databricks, PySpark, dbt | Pharma & Life Sciences Aspirant",
                summary=(
                    "Results-oriented Data Engineer with hands-on expertise in Python, SQL, Snowflake, Databricks, "
                    "PySpark, and dbt. Specialized in designing Medallion Architecture pipelines, ETL/ELT workflows, "
                    "and automated data quality validation. Passionate about applying scalable data engineering "
                    "practices to pharmaceutical, healthcare, and clinical data systems."
                ),
                phone="+91-6303362149",
                linkedin_url="https://linkedin.com/in/demo-candidate",
                github_url="https://github.com/demo-candidate",
                total_experience_years=0.5,  # Fresher / 0-1 year
                current_location="Hyderabad",
                willing_to_relocate=True,
                employment_preferences=["Full-time", "Hybrid", "Remote"],
                verified_by_candidate=True  # Candidate confirmed initial profile
            )
            db.add(profile)
            db.flush()

            # Education
            edu = CandidateEducation(
                profile_id=profile.id,
                degree="B.Tech",
                field_of_study="Computer Science and Engineering",
                institution="Jawaharlal Nehru Technological University",
                start_year=2020,
                end_year=2024,
                cgpa_or_percentage=8.4,
                is_highest=True
            )
            db.add(edu)

            # Technical Skills (from Section 8)
            skills_data = [
                ("Python", "Programming", "Advanced", 1.5),
                ("SQL", "Database", "Advanced", 1.5),
                ("Java", "Programming", "Intermediate", 1.0),
                ("Snowflake", "Cloud & DWH", "Intermediate", 1.0),
                ("Databricks", "Big Data & AI", "Intermediate", 1.0),
                ("PySpark", "Big Data & AI", "Intermediate", 1.0),
                ("dbt", "Data Modeling", "Intermediate", 1.0),
                ("Power BI", "BI & Visualization", "Intermediate", 1.0),
                ("Tableau", "BI & Visualization", "Intermediate", 1.0),
                ("Microsoft Fabric", "Cloud & DWH", "Intermediate", 0.8),
                ("ETL", "Data Engineering", "Advanced", 1.5),
                ("Git", "Tools & DevOps", "Intermediate", 1.5),
                ("REST APIs", "Integration", "Intermediate", 1.2),
            ]
            for s_name, s_cat, s_prof, s_exp in skills_data:
                db.add(CandidateSkill(
                    profile_id=profile.id,
                    name=s_name,
                    category=s_cat,
                    proficiency=s_prof,
                    years_experience=s_exp,
                    verified=True
                ))

            # Projects (from Section 8)
            projects_data = [
                {
                    "title": "Retail & Pharma Supply Chain Medallion Pipeline",
                    "role": "Lead Data Pipeline Developer",
                    "domain": "Data Engineering & Analytics",
                    "description": (
                        "Engineered end-to-end Medallion Architecture (Bronze -> Silver -> Gold) data lakehouse on "
                        "Databricks with PySpark and Delta Lake. Ingested transactional and batch data, enforcing schema "
                        "evolution and ACID compliance."
                    ),
                    "technologies": ["Python", "PySpark", "Databricks", "Delta Lake", "SQL"],
                    "highlights": [
                        "Reduced query latency by 42% using Z-ordering and optimized file partitioning.",
                        "Implemented automated streaming ingestion with structured streaming."
                    ]
                },
                {
                    "title": "Automated Data Quality Validation & Anomaly Detection",
                    "role": "Data Engineer",
                    "domain": "Data Quality & Governance",
                    "description": (
                        "Created robust automated data validation pipelines using Python and Great Expectations/SQL assertions "
                        "to intercept corrupted records before landing in production data marts."
                    ),
                    "technologies": ["Python", "SQL", "Snowflake", "Great Expectations", "REST APIs"],
                    "highlights": [
                        "Ensured 99.8% data fidelity across 500k+ daily records.",
                        "Configured automated alerting webhooks for schema violations."
                    ]
                },
                {
                    "title": "Cloud Data Mart & Transformation with Snowflake and dbt",
                    "role": "Analytics Engineer",
                    "domain": "Data Warehousing & BI",
                    "description": (
                        "Architected modular dimensional models (Star Schema) in Snowflake utilizing dbt Core for ELT "
                        "transformations, version-controlled testing, and automated documentation generation."
                    ),
                    "technologies": ["Snowflake", "dbt", "SQL", "Git", "Power BI"],
                    "highlights": [
                        "Modeled 15+ dimensional tables and fact tables with incremental models.",
                        "Connected curated Gold layers to Power BI dashboards for operational KPIs."
                    ]
                }
            ]
            for p in projects_data:
                db.add(CandidateProject(
                    profile_id=profile.id,
                    title=p["title"],
                    role=p["role"],
                    domain=p["domain"],
                    description=p["description"],
                    technologies=p["technologies"],
                    highlights=p["highlights"]
                ))

            # Initial welcome notification
            db.add(Notification(
                user_id=demo_user.id,
                title="Welcome to Pharma Job Hunter AI",
                message="Your profile has been created. The autonomous agent is ready to discover data roles across India's pharmaceutical ecosystem.",
                notification_type="SystemAlert",
                channel="dashboard",
                is_read=False
            ))

            db.commit()
            print("   Demo candidate profile and initial portfolio successfully seeded!")
        else:
            print("   Demo candidate already exists. Skipping.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

