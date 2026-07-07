"""Health/status endpoints. /api/status will grow job-run summaries in Phase 2+."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["status"])


@router.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@router.get("/api/status")
def status_page():
    # Phase 2+: report last scrape/price-refresh job runs here.
    return {"service": "fintrack-api", "phase": 1, "jobs": {}}
