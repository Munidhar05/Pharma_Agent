import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import (
    User,
    CandidateProfile,
    CandidateSkill,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    CandidateResume,
    Notification
)
from backend.app.schemas.candidate import (
    CandidateProfileDetailResponse,
    CandidateProfileUpdate,
    CandidateSkillCreate,
    CandidateSkillResponse,
    CandidateEducationResponse,
    CandidateExperienceResponse,
    CandidateProjectCreate,
    CandidateProjectResponse,
    CandidateResumeResponse,
    ResumeUploadResponse
)
from backend.app.services.resume_parser import ResumeParserService
from backend.app.agents.candidate_profile import CandidateProfileAgent

router = APIRouter(prefix="/candidate", tags=["Candidate Profile"])


def get_current_candidate_profile(db: Session = Depends(get_db)) -> CandidateProfile:
    """Helper to retrieve the primary candidate profile (demo candidate or authenticated user)."""
    profile = db.query(CandidateProfile).first()
    if not profile:
        # Fallback create default if not present
        demo_user = db.query(User).filter(User.role == "candidate").first()
        if not demo_user:
            demo_user = User(
                email="kandulamunidharreddy@gmail.com",
                password_hash="placeholder",
                full_name="Candidate Demo",
                role="candidate"
            )
            db.add(demo_user)
            db.flush()
        profile = CandidateProfile(user_id=demo_user.id, headline="Data Engineer Aspirant")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/profile", response_model=CandidateProfileDetailResponse)
def get_profile(
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Retrieve full candidate profile with skills, education, experience, projects, and verification status."""
    return CandidateProfileDetailResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.user.full_name,
        email=profile.user.email,
        headline=profile.headline,
        summary=profile.summary,
        phone=profile.phone,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        total_experience_years=profile.total_experience_years,
        current_ctc=profile.current_ctc,
        expected_ctc=profile.expected_ctc,
        notice_period_days=profile.notice_period_days,
        current_location=profile.current_location,
        willing_to_relocate=profile.willing_to_relocate,
        employment_preferences=profile.employment_preferences or [],
        verified_by_candidate=profile.verified_by_candidate,
        skills=[CandidateSkillResponse.model_validate(s) for s in profile.skills],
        education=[CandidateEducationResponse.model_validate(e) for e in profile.education],
        experience=[CandidateExperienceResponse.model_validate(ex) for ex in profile.experience],
        projects=[CandidateProjectResponse.model_validate(p) for p in profile.projects],
        resumes=[CandidateResumeResponse.model_validate(r) for r in profile.resumes],
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.put("/profile", response_model=CandidateProfileDetailResponse)
def update_profile(
    payload: CandidateProfileUpdate,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Update editable candidate profile information."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return get_profile(db=db, profile=profile)


@router.post("/profile/verify")
def verify_candidate_profile(
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Explicit candidate verification confirming extracted information is 100% truthful and accurate."""
    profile.verified_by_candidate = True
    db.commit()

    agent = CandidateProfileAgent(profile)
    analysis = agent.analyze_profile()

    return {
        "status": "success",
        "message": "Candidate profile successfully confirmed and verified.",
        "verified_by_candidate": True,
        "completeness_score": analysis["completeness_score"],
        "readiness_status": analysis["status"]
    }


@router.get("/profile/analysis")
def get_profile_analysis(
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Execute Agent 5 (Candidate Profile Agent) to evaluate readiness, missing fields, and pharma relevance."""
    agent = CandidateProfileAgent(profile)
    return agent.analyze_profile()


@router.post("/upload-resume", response_model=ResumeUploadResponse)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """
    Upload a candidate resume in PDF or DOCX format.
    Extracts text, parses skills, education, and projects, and stores file securely.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Please upload a PDF or DOCX file."
        )

    # Save to storage
    file_path = os.path.join(settings.UPLOAD_DIR, f"{profile.id}_{file.filename}")
    content = file.file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    file_size = len(content)

    # Parse resume
    try:
        parsed_data = ResumeParserService.parse_resume(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume parsing error: {str(e)}"
        )

    # Create Resume record
    resume_record = CandidateResume(
        profile_id=profile.id,
        file_path=file_path,
        original_filename=file.filename,
        file_size_bytes=file_size,
        file_type="application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        parsed_raw_text=parsed_data.get("raw_text", ""),
        is_primary=True
    )
    db.add(resume_record)

    # Update user identity and contact fields if discovered in resume
    if parsed_data.get("name"):
        profile.user.full_name = parsed_data["name"]
    if parsed_data.get("email"):
        profile.user.email = parsed_data["email"]
    if parsed_data.get("phone"):
        profile.phone = parsed_data["phone"]
    if parsed_data.get("location"):
        profile.current_location = parsed_data["location"]
    if parsed_data.get("headline"):
        profile.headline = parsed_data["headline"]
    if parsed_data.get("linkedin_url"):
        profile.linkedin_url = parsed_data["linkedin_url"]
    if parsed_data.get("github_url"):
        profile.github_url = parsed_data["github_url"]
    if parsed_data.get("total_experience_years") is not None:
        profile.total_experience_years = parsed_data["total_experience_years"]
    if parsed_data.get("notice_period_days") is not None:
        profile.notice_period_days = parsed_data["notice_period_days"]

    # Ingest extracted skills from the resume (refreshing skill inventory)
    if parsed_data.get("skills"):
        db.query(CandidateSkill).filter(CandidateSkill.profile_id == profile.id).delete()
        for sk in parsed_data["skills"]:
            db.add(CandidateSkill(
                profile_id=profile.id,
                name=sk["name"],
                category=sk["category"],
                proficiency=sk.get("proficiency", "Intermediate"),
                years_experience=sk.get("years_experience", 1.0),
                verified=True
            ))

    # Ingest education from the resume
    if parsed_data.get("education"):
        db.query(CandidateEducation).filter(CandidateEducation.profile_id == profile.id).delete()
        for edu in parsed_data["education"]:
            db.add(CandidateEducation(
                profile_id=profile.id,
                degree=edu["degree"],
                field_of_study=edu["field_of_study"],
                institution=edu.get("institution", "University / College"),
                start_year=edu.get("start_year"),
                end_year=edu.get("end_year"),
                cgpa_or_percentage=edu.get("cgpa_or_percentage"),
                is_highest=edu.get("is_highest", True)
            ))

    # Ingest projects if discovered
    if parsed_data.get("projects"):
        db.query(CandidateProject).filter(CandidateProject.profile_id == profile.id).delete()
        for pr in parsed_data["projects"]:
            db.add(CandidateProject(
                profile_id=profile.id,
                title=pr["title"],
                role=pr.get("role", "Data Engineer"),
                domain=pr.get("domain", "Data Engineering"),
                description=pr.get("description", ""),
                technologies=pr.get("technologies", []),
                highlights=pr.get("highlights", [])
            ))

    db.commit()
    db.refresh(profile)

    # Recalculate job match scores with candidate's newly parsed resume profile
    try:
        from backend.app.agents.job_matching import JobMatchingAgent
        matcher = JobMatchingAgent(db=db)
        matcher.evaluate_all_active_jobs(candidate=profile)
    except Exception:
        pass

    agent = CandidateProfileAgent(profile)
    analysis = agent.analyze_profile()

    return ResumeUploadResponse(
        message=f"Resume uploaded and parsed successfully. Profile updated for {profile.user.full_name}.",
        resume_id=resume_record.id,
        filename=file.filename,
        file_type=ext,
        extracted_data_summary={
            "name": profile.user.full_name,
            "email": profile.user.email,
            "phone": profile.phone,
            "location": profile.current_location,
            "headline": profile.headline,
            "skills_found": len(parsed_data.get("skills", [])),
            "projects_found": len(parsed_data.get("projects", [])),
            "education_found": len(parsed_data.get("education", [])),
            "linkedin": parsed_data.get("linkedin_url"),
            "github": parsed_data.get("github_url"),
        },
        profile_completeness_score=analysis["completeness_score"],
        verification_required=True
    )


# Skills CRUD
@router.post("/skills", response_model=CandidateSkillResponse)
def add_skill(
    skill_in: CandidateSkillCreate,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Add a new technical skill to candidate profile."""
    existing = db.query(CandidateSkill).filter(
        CandidateSkill.profile_id == profile.id,
        CandidateSkill.name.ilike(skill_in.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Skill already exists in profile.")

    skill = CandidateSkill(
        profile_id=profile.id,
        name=skill_in.name,
        category=skill_in.category,
        proficiency=skill_in.proficiency,
        years_experience=skill_in.years_experience,
        verified=skill_in.verified
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}")
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Delete a skill from candidate profile."""
    skill = db.query(CandidateSkill).filter(
        CandidateSkill.id == skill_id,
        CandidateSkill.profile_id == profile.id
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found.")

    db.delete(skill)
    db.commit()
    return {"status": "success", "message": f"Skill '{skill.name}' deleted."}


# Projects CRUD
@router.post("/projects", response_model=CandidateProjectResponse)
def add_project(
    project_in: CandidateProjectCreate,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Add a technical project to candidate profile."""
    project = CandidateProject(
        profile_id=profile.id,
        title=project_in.title,
        role=project_in.role,
        domain=project_in.domain,
        description=project_in.description,
        technologies=project_in.technologies,
        repo_url=project_in.repo_url,
        live_url=project_in.live_url,
        highlights=project_in.highlights
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """Delete a project from candidate profile."""
    project = db.query(CandidateProject).filter(
        CandidateProject.id == project_id,
        CandidateProject.profile_id == profile.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    db.delete(project)
    db.commit()
    return {"status": "success", "message": f"Project '{project.title}' deleted."}


@router.get("/resumes", response_model=List[CandidateResumeResponse])
def list_resumes(
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """List all uploaded resumes."""
    return profile.resumes
