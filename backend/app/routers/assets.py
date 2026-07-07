"""Asset universe endpoints: search/list, detail, price history."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.logging_config import app_log
from app.models import Asset, AssetType, PriceHistory
from app.schemas import (
    AssetHistoryResponse,
    AssetListResponse,
    AssetResponse,
    PriceBar,
    TickerEntry,
)
from app.services.market_data import backfill_history, history_is_stale

router = APIRouter(prefix="/api", tags=["assets"])

RANGE_DAYS = {"1m": 31, "3m": 92, "6m": 183, "1y": 366, "2y": 731, "max": None}

SORT_COLUMNS = {
    "symbol": Asset.symbol,
    "name": Asset.name,
    "price": Asset.last_price,
    "change": Asset.day_change_pct,
    "market_cap": Asset.market_cap,
}


@router.get("/assets", response_model=AssetListResponse)
def list_assets(
    q: str | None = Query(None, max_length=100, description="search symbol or name"),
    asset_type: AssetType | None = Query(None),
    sort: str = Query("symbol", pattern="^(symbol|name|price|change|market_cap)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Asset)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Asset.symbol.ilike(pattern), Asset.name.ilike(pattern)))
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    direction = desc if order == "desc" else asc
    column = SORT_COLUMNS[sort]
    # NULL prices/changes sort last regardless of direction.
    query = query.order_by(column.is_(None), direction(column), Asset.symbol)
    items = list(db.scalars(query.limit(limit).offset(offset)))
    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def _get_asset_or_404(db: Session, symbol: str) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.symbol == symbol.upper()))
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.get("/assets/{symbol}", response_model=AssetResponse)
def get_asset(symbol: str, db: Session = Depends(get_db)):
    return _get_asset_or_404(db, symbol)


@router.get("/assets/{symbol}/history", response_model=AssetHistoryResponse)
def get_asset_history(
    symbol: str,
    range: str = Query("1y", pattern="^(1m|3m|6m|1y|2y|max)$"),
    db: Session = Depends(get_db),
):
    asset = _get_asset_or_404(db, symbol)

    # On-demand refresh for the viewed asset (spec 2.3). Best-effort: serve
    # whatever is stored if the provider is unreachable.
    if history_is_stale(db, asset):
        try:
            backfill_history(db, asset)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            app_log.warning("on_demand_history_failed", symbol=asset.symbol, error=str(exc))

    query = (
        select(PriceHistory)
        .where(PriceHistory.asset_id == asset.id)
        .order_by(PriceHistory.ts)
    )
    days = RANGE_DAYS[range]
    if days is not None:
        query = query.where(PriceHistory.ts >= datetime.now(UTC) - timedelta(days=days))
    bars = list(db.scalars(query))
    return AssetHistoryResponse(
        symbol=asset.symbol,
        range=range,
        bars=[PriceBar.model_validate(b) for b in bars],
    )


@router.get("/market/ticker", response_model=list[TickerEntry])
def market_ticker(limit: int = Query(10, ge=1, le=30), db: Session = Depends(get_db)):
    """Top movers (by absolute day change) for the landing-page strip. Public."""
    assets = db.scalars(
        select(Asset)
        .where(Asset.day_change_pct.is_not(None))
        .order_by(func.abs(Asset.day_change_pct).desc())
        .limit(limit)
    )
    return [
        TickerEntry(
            symbol=a.symbol,
            asset_type=a.asset_type,
            last_price=a.last_price,
            day_change_pct=a.day_change_pct,
        )
        for a in assets
    ]
