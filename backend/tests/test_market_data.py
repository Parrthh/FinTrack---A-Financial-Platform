"""Market-data service tests (providers monkeypatched, no network)."""

from datetime import UTC, datetime, timedelta

from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Asset, PriceHistory
from app.providers.stooq import Bar
from app.services import market_data

settings = get_settings()


def test_backfill_drops_history_beyond_cap(client, monkeypatch):
    db = next(app.dependency_overrides[get_db]())
    asset = Asset(symbol="AAPL", name="Apple Inc.", asset_type="stock")
    db.add(asset)
    db.commit()

    now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    ancient = now - timedelta(days=settings.history_max_days + 100)
    recent = now - timedelta(days=10)

    def fake_history(symbol):
        return [
            Bar(ts=ancient, open=1, high=1, low=1, close=1.0, volume=1),
            Bar(ts=recent, open=2, high=2, low=2, close=2.0, volume=2),
        ]

    monkeypatch.setattr(market_data.stooq, "fetch_daily_history", fake_history)

    stored = market_data.backfill_history(db, asset)
    assert stored == 1
    rows = db.query(PriceHistory).filter_by(asset_id=asset.id).all()
    assert len(rows) == 1
    assert rows[0].close == 2.0
