"""Seed the asset universe and (optionally) price data.

Usage:
    python -m app.seed                  # insert universe assets only
    python -m app.seed --backfill      # + fetch real history & quotes (needs network)
    python -m app.seed --demo-data     # + generate synthetic prices (offline dev ONLY)

--demo-data exists so local dev works without provider access; it labels
nothing as real and must never run against a production database.
"""

import argparse
import math
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models import Asset, AssetType, PriceHistory
from app.services.market_data import (
    backfill_all_history,
    refresh_crypto_prices,
    refresh_stock_prices,
    seed_universe,
)

DEMO_DAYS = 730


def generate_demo_history(db, asset: Asset) -> None:
    """Synthetic-but-plausible daily OHLCV via a seeded random walk."""
    rng = random.Random(asset.symbol)  # deterministic per symbol
    base = {
        AssetType.stock: rng.uniform(40, 600),
        AssetType.etf: rng.uniform(80, 550),
        AssetType.crypto: rng.uniform(0.5, 90000),
    }[asset.asset_type]

    db.execute(delete(PriceHistory).where(PriceHistory.asset_id == asset.id))
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    price = base
    rows = []
    for i in range(DEMO_DAYS, 0, -1):
        drift = rng.gauss(0.0004, 0.02)
        price = max(price * math.exp(drift), 0.01)
        spread = price * abs(rng.gauss(0, 0.012))
        open_ = price * (1 + rng.gauss(0, 0.006))
        rows.append(
            PriceHistory(
                asset_id=asset.id,
                ts=today - timedelta(days=i),
                open=round(open_, 4),
                high=round(max(open_, price) + spread, 4),
                low=round(max(min(open_, price) - spread, 0.01), 4),
                close=round(price, 4),
                volume=round(rng.uniform(1e5, 5e7)),
            )
        )
    db.add_all(rows)

    prev_close = rows[-2].close
    asset.last_price = rows[-1].close
    asset.last_price_at = datetime.now(UTC)
    asset.day_change_pct = (rows[-1].close - prev_close) / prev_close * 100
    if asset.asset_type == AssetType.crypto:
        asset.market_cap = round(asset.last_price * rng.uniform(1e7, 2e10))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backfill", action="store_true", help="fetch real prices/history")
    parser.add_argument(
        "--demo-data", action="store_true", help="generate synthetic prices (dev only)"
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        added = seed_universe(db)
        print(f"Universe seeded ({added} new assets).")

        if args.demo_data:
            assets = list(db.scalars(select(Asset)))
            for asset in assets:
                generate_demo_history(db, asset)
            print(f"Demo price data generated for {len(assets)} assets (synthetic!).")

        if args.backfill:
            run = backfill_all_history(db)
            print(f"History backfill: {run.status}, {run.items_processed} bars.")
            crypto = refresh_crypto_prices(db)
            print(f"Crypto refresh: {crypto.status}, {crypto.items_processed} assets.")
            stocks = refresh_stock_prices(db)
            print(f"Stock refresh: {stocks.status}, {stocks.items_processed} assets.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
