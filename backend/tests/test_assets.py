"""Asset universe endpoint tests (seeded in-memory DB, no network)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.database import get_db
from app.main import app
from app.models import Asset, PriceHistory


def _db(client):
    return next(app.dependency_overrides[get_db]())


@pytest.fixture()
def seeded(client):
    from app.services.market_data import seed_universe

    db = _db(client)
    seed_universe(db)
    # Give AAPL a price + fresh history so list/detail/history have data.
    aapl = db.query(Asset).filter_by(symbol="AAPL").one()
    aapl.last_price = 212.44
    aapl.day_change_pct = 0.82
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(400):
        db.add(
            PriceHistory(
                asset_id=aapl.id, ts=today - timedelta(days=i), close=200 + (i % 30)
            )
        )
    btc = db.query(Asset).filter_by(symbol="BTC").one()
    btc.last_price = 97214.0
    btc.day_change_pct = -1.92
    btc.market_cap = 1.9e12
    db.commit()
    return client


def test_list_assets_paginates(seeded):
    res = seeded.get("/api/assets?limit=10")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] > 90
    assert len(body["items"]) == 10


def test_list_assets_search(seeded):
    body = seeded.get("/api/assets?q=apple").json()
    assert any(a["symbol"] == "AAPL" for a in body["items"])
    body = seeded.get("/api/assets?q=BTC").json()
    assert any(a["symbol"] == "BTC" for a in body["items"])


def test_list_assets_filter_and_sort(seeded):
    body = seeded.get("/api/assets?asset_type=crypto&sort=market_cap&order=desc").json()
    assert all(a["asset_type"] == "crypto" for a in body["items"])
    assert body["items"][0]["symbol"] == "BTC"  # only one with market cap set


def test_list_assets_rejects_bad_sort(seeded):
    assert seeded.get("/api/assets?sort=evil").status_code == 422


def test_asset_detail(seeded):
    res = seeded.get("/api/assets/aapl")  # case-insensitive
    assert res.status_code == 200
    assert res.json()["name"] == "Apple Inc."
    assert seeded.get("/api/assets/NOPE").status_code == 404


def test_asset_history_ranges(seeded):
    year = seeded.get("/api/assets/AAPL/history?range=1y").json()
    month = seeded.get("/api/assets/AAPL/history?range=1m").json()
    assert 360 <= len(year["bars"]) <= 400
    assert 28 <= len(month["bars"]) <= 32
    assert year["bars"][0]["ts"] < year["bars"][-1]["ts"]


def test_ticker_returns_top_movers(seeded):
    body = seeded.get("/api/market/ticker").json()
    symbols = [t["symbol"] for t in body]
    assert "BTC" in symbols and "AAPL" in symbols
    # BTC has the larger |day change|, so it comes first.
    assert symbols.index("BTC") < symbols.index("AAPL")


def test_job_endpoints_require_token(seeded):
    assert seeded.post("/api/jobs/refresh-prices").status_code == 403
    assert (
        seeded.post(
            "/api/jobs/refresh-prices", headers={"X-Job-Token": "wrong"}
        ).status_code
        == 403
    )


def test_status_page_reports_job_runs(seeded):
    from app.models import JobRun

    db = _db(seeded)
    db.add(JobRun(job_name="refresh_crypto_prices", status="success", items_processed=20))
    db.commit()
    body = seeded.get("/api/status").json()
    assert body["jobs"]["refresh_crypto_prices"]["status"] == "success"
    assert body["jobs"]["refresh_crypto_prices"]["items_processed"] == 20
