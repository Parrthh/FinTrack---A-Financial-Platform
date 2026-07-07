"""Market-data service: universe seeding, price refresh, history backfill.

Provider etiquette: the whole crypto universe is one CoinGecko call; stock
quotes batch 20 symbols per Stooq call; per-symbol history fetches sleep
briefly between requests. All jobs record a JobRun row surfaced on /api/status.
"""

import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import universe
from app.config import get_settings
from app.logging_config import jobs_log
from app.models import Asset, AssetType, JobRun, PriceHistory
from app.providers import coingecko, stooq

settings = get_settings()

HISTORY_FETCH_DELAY_SECONDS = 0.25


def seed_universe(db: Session) -> int:
    """Insert any missing universe assets. Idempotent; returns rows added."""
    existing = set(db.scalars(select(Asset.symbol)))
    added = 0
    for symbol, name, exchange, sector in universe.STOCKS:
        if symbol not in existing:
            db.add(
                Asset(
                    symbol=symbol,
                    name=name,
                    asset_type=AssetType.stock,
                    exchange=exchange,
                    sector=sector,
                )
            )
            added += 1
    for symbol, name, exchange in universe.ETFS:
        if symbol not in existing:
            db.add(Asset(symbol=symbol, name=name, asset_type=AssetType.etf, exchange=exchange))
            added += 1
    for symbol, name, coingecko_id in universe.CRYPTO:
        if symbol not in existing:
            db.add(
                Asset(
                    symbol=symbol,
                    name=name,
                    asset_type=AssetType.crypto,
                    provider_ref=coingecko_id,
                )
            )
            added += 1
    db.commit()
    return added


def _start_job(db: Session, job_name: str) -> JobRun:
    run = JobRun(job_name=job_name)
    db.add(run)
    db.commit()
    return run


def _finish_job(db: Session, run: JobRun, items: int, error: str | None = None) -> None:
    run.status = "error" if error else "success"
    run.items_processed = items
    run.error = error
    run.finished_at = datetime.now(UTC)
    db.commit()
    log = jobs_log.error if error else jobs_log.info
    log(
        "job_finished",
        job=run.job_name,
        status=run.status,
        items=items,
        **({"error": error} if error else {}),
    )


def refresh_crypto_prices(db: Session) -> JobRun:
    """Update last price / day change / market cap for all crypto assets."""
    run = _start_job(db, "refresh_crypto_prices")
    assets = list(
        db.scalars(select(Asset).where(Asset.asset_type == AssetType.crypto))
    )
    by_ref = {a.provider_ref: a for a in assets if a.provider_ref}
    try:
        markets = coingecko.fetch_markets(list(by_ref))
        now = datetime.now(UTC)
        updated = 0
        for m in markets:
            asset = by_ref.get(m.coingecko_id)
            if asset is None:
                continue
            asset.last_price = m.price
            asset.last_price_at = now
            asset.day_change_pct = m.day_change_pct
            asset.market_cap = m.market_cap
            updated += 1
        db.commit()
        _finish_job(db, run, updated)
    except Exception as exc:  # noqa: BLE001 — job must record any failure
        db.rollback()
        _finish_job(db, run, 0, error=str(exc))
    return run


def refresh_stock_prices(db: Session) -> JobRun:
    """Update last price / day change for all stock and ETF assets.

    Day change compares the quote close against the most recent *prior* close
    in price_history (needs history backfilled to be meaningful).
    """
    run = _start_job(db, "refresh_stock_prices")
    assets = list(
        db.scalars(
            select(Asset).where(Asset.asset_type.in_([AssetType.stock, AssetType.etf]))
        )
    )
    by_symbol = {a.symbol: a for a in assets}
    try:
        quotes = stooq.fetch_quotes(list(by_symbol))
        now = datetime.now(UTC)
        updated = 0
        for q in quotes:
            asset = by_symbol.get(q.symbol)
            if asset is None:
                continue
            asset.last_price = q.close
            asset.last_price_at = now
            prev_close = db.scalar(
                select(PriceHistory.close)
                .where(PriceHistory.asset_id == asset.id, PriceHistory.ts < q.ts)
                .order_by(PriceHistory.ts.desc())
                .limit(1)
            )
            if prev_close:
                asset.day_change_pct = (q.close - prev_close) / prev_close * 100
            # Upsert today's bar so history stays current between backfills.
            db.merge(
                PriceHistory(
                    asset_id=asset.id,
                    ts=q.ts.replace(hour=0, minute=0, second=0, microsecond=0),
                    open=q.open,
                    high=q.high,
                    low=q.low,
                    close=q.close,
                    volume=q.volume,
                )
            )
            updated += 1
        db.commit()
        _finish_job(db, run, updated)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        _finish_job(db, run, 0, error=str(exc))
    return run


def backfill_history(db: Session, asset: Asset) -> int:
    """Replace an asset's stored daily history from its provider.

    History older than history_max_days is dropped so the database stays
    within free-tier storage limits.
    """
    cutoff = datetime.now(UTC) - timedelta(days=settings.history_max_days)
    if asset.asset_type == AssetType.crypto:
        if not asset.provider_ref:
            return 0
        points = coingecko.fetch_daily_history(asset.provider_ref)
        rows = [
            PriceHistory(
                asset_id=asset.id,
                ts=p.ts.replace(hour=0, minute=0, second=0, microsecond=0),
                close=p.price,
                volume=p.volume,
            )
            for p in points
            if p.ts >= cutoff
        ]
    else:
        bars = stooq.fetch_daily_history(asset.symbol)
        rows = [
            PriceHistory(
                asset_id=asset.id,
                ts=b.ts,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
            )
            for b in bars
            if b.ts >= cutoff
        ]
    # Keep one bar per day: replace wholesale (simple + idempotent).
    db.execute(delete(PriceHistory).where(PriceHistory.asset_id == asset.id))
    db.add_all(rows)
    db.commit()
    return len(rows)


def backfill_all_history(db: Session) -> JobRun:
    """Backfill daily history for every asset (run once after seeding, then daily)."""
    run = _start_job(db, "backfill_history")
    total = 0
    errors: list[str] = []
    for asset in db.scalars(select(Asset)):
        try:
            total += backfill_history(db, asset)
        except Exception as exc:  # noqa: BLE001 — keep going, report at the end
            db.rollback()
            errors.append(f"{asset.symbol}: {exc}")
        time.sleep(HISTORY_FETCH_DELAY_SECONDS)
    _finish_job(db, run, total, error="; ".join(errors[:10]) or None)
    return run


def history_is_stale(db: Session, asset: Asset) -> bool:
    latest = db.scalar(
        select(func.max(PriceHistory.ts)).where(PriceHistory.asset_id == asset.id)
    )
    if latest is None:
        return True
    if latest.tzinfo is None:  # SQLite drops tzinfo
        latest = latest.replace(tzinfo=UTC)
    return datetime.now(UTC) - latest > timedelta(seconds=settings.history_stale_seconds)
