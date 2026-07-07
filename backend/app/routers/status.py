"""Health/status endpoints. /api/status surfaces the latest run per job."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JobRun
from app.schemas import JobRunResponse

router = APIRouter(tags=["status"])


@router.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@router.get("/api/status")
def status_page(db: Session = Depends(get_db)):
    """Owner-facing job dashboard (spec 8.2): last run per job name."""
    job_names = db.scalars(select(JobRun.job_name).distinct())
    jobs = {}
    for name in job_names:
        last = db.scalar(
            select(JobRun)
            .where(JobRun.job_name == name)
            .order_by(JobRun.started_at.desc())
            .limit(1)
        )
        if last:
            jobs[name] = JobRunResponse.model_validate(last).model_dump(mode="json")
    return {"service": "fintrack-api", "phase": 2, "jobs": jobs}
