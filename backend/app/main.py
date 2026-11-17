from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Autonomous AI Agent for Pharmaceutical Data Job Discovery, ATS Resume Optimization, and Auto-Application in India.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files for Embedded Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify database and service connectivity."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
        "freshness_period_days": settings.JOB_FRESHNESS_DAYS,
        "application_mode": settings.APPLICATION_MODE
    }


@app.get("/dashboard", tags=["UI"])
def dashboard():
    """Serves the interactive single-page application dashboard."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, media_type="text/html")
    return {"message": "Dashboard UI static file not found"}


@app.get("/jobs", include_in_schema=False)
def redirect_jobs():
    return RedirectResponse(url="/dashboard")


@app.get("/applications", include_in_schema=False)
def redirect_applications():
    return RedirectResponse(url="/dashboard")


@app.get("/profile", include_in_schema=False)
def redirect_profile():
    return RedirectResponse(url="/dashboard")


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API Gateway",
        "dashboard_url": "/dashboard",
        "docs_url": "/docs",
        "health_check": "/health"
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
