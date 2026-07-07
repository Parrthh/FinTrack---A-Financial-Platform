"""CoinGecko client — free, keyless crypto prices (genuinely near-real-time).

Free tier allows a handful of calls per minute; the whole crypto universe fits
in a single /coins/markets call, so refreshes stay comfortably inside limits.
Parsing is separated from fetching so tests can run on recorded JSON fixtures.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class CoinMarket:
    coingecko_id: str
    price: float
    market_cap: float | None
    day_change_pct: float | None


@dataclass
class PricePoint:
    ts: datetime
    price: float
    volume: float | None


def parse_markets(data: list[dict]) -> list[CoinMarket]:
    markets = []
    for item in data:
        if item.get("current_price") is None:
            continue
        markets.append(
            CoinMarket(
                coingecko_id=item["id"],
                price=float(item["current_price"]),
                market_cap=item.get("market_cap"),
                day_change_pct=item.get("price_change_percentage_24h"),
            )
        )
    return markets


def parse_market_chart(data: dict) -> list[PricePoint]:
    """Parse /market_chart: {"prices": [[ms, price]...], "total_volumes": [[ms, v]...]}."""
    volumes = {int(ts): v for ts, v in data.get("total_volumes", [])}
    points = []
    for ts_ms, price in data.get("prices", []):
        points.append(
            PricePoint(
                ts=datetime.fromtimestamp(ts_ms / 1000, tz=UTC),
                price=float(price),
                volume=volumes.get(int(ts_ms)),
            )
        )
    return points


def fetch_markets(coingecko_ids: list[str]) -> list[CoinMarket]:
    with httpx.Client(timeout=settings.provider_timeout_seconds) as client:
        res = client.get(
            f"{settings.coingecko_base_url}/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": ",".join(coingecko_ids),
                "per_page": len(coingecko_ids),
                "page": 1,
            },
        )
        res.raise_for_status()
        return parse_markets(res.json())


def fetch_daily_history(coingecko_id: str, days: int = 365) -> list[PricePoint]:
    with httpx.Client(timeout=settings.provider_timeout_seconds) as client:
        res = client.get(
            f"{settings.coingecko_base_url}/api/v3/coins/{coingecko_id}/market_chart",
            params={"vs_currency": "usd", "days": days, "interval": "daily"},
        )
        res.raise_for_status()
        return parse_market_chart(res.json())
