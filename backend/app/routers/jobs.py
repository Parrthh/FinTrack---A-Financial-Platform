"""Job trigger endpoints, called by GitHub Actions cron (free scheduler).

Render's free tier has no free background workers or cron, so scheduled work
arrives as authenticated HTTP calls: a scheduled GitHub Actions workflow hits
these endpoints with the shared JOB_TOKEN. Calls also wake the free-tier
service if it has spun down.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import JobRunResponse
from app.services.market_data import (
    backfill_all_history,
    refresh_crypto_prices,
    refresh_stock_prices,
    seed_universe,
)

settings = get_settings()
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def require_job_token(x_job_token: str | None = Header(None)) -> None:
    if not settings.job_token or x_job_token != settings.job_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid job token")


@router.post(
    "/refresh-prices",
    response_model=list[JobRunResponse],
    dependencies=[Depends(require_job_token)],
)
def refresh_prices(db: Session = Depends(get_db)):
    """Refresh crypto + stock/ETF quotes (fast; run every ~30-60 min)."""
    seed_universe(db)  # picks up any newly added universe entries
    return [
        JobRunResponse.model_validate(refresh_crypto_prices(db)),
        JobRunResponse.model_validate(refresh_stock_prices(db)),
    ]


@router.post(
    "/backfill-history",
    response_model=JobRunResponse,
    dependencies=[Depends(require_job_token)],
)
def backfill(db: Session = Depends(get_db)):
    """Full daily-history backfill for every asset (slow; run daily)."""
    seed_universe(db)
    return JobRunResponse.model_validate(backfill_all_history(db))
