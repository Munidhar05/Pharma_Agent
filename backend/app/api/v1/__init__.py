from fastapi import APIRouter
from backend.app.api.v1.candidate import router as candidate_router
from backend.app.api.v1.companies import router as companies_router
from backend.app.api.v1.jobs import router as jobs_router
from backend.app.api.v1.matching import router as matching_router
from backend.app.api.v1.resumes import router as resumes_router
from backend.app.api.v1.applications import router as applications_router
from backend.app.api.v1.notifications import router as notifications_router

api_router = APIRouter()
api_router.include_router(candidate_router)
api_router.include_router(companies_router)
api_router.include_router(jobs_router)
api_router.include_router(matching_router)
api_router.include_router(resumes_router)
api_router.include_router(applications_router)
api_router.include_router(notifications_router)


