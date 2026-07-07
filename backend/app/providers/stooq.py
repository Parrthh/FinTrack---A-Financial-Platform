"""Stooq client — free, keyless source for stock/ETF quotes and daily history.

Data is end-of-day / delayed (never real-time); the UI labels it as such.
Parsing is separated from fetching so tests can run on recorded CSV fixtures.
Stooq symbol convention for US listings: lowercase with a `.us` suffix, and
dots in tickers become dashes (BRK.B -> brk-b.us).
"""

import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime
from datetime import time as dtime

import httpx

from app.config import get_settings

settings = get_settings()

# Batch size for the multi-symbol quote endpoint; kept small to be polite.
QUOTE_BATCH_SIZE = 20


@dataclass
class Quote:
    symbol: str  # our symbol, e.g. "AAPL"
    ts: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: float | None


@dataclass
class Bar:
    ts: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: float | None


def to_stooq_symbol(symbol: str) -> str:
    return f"{symbol.lower().replace('.', '-')}.us"


def from_stooq_symbol(stooq_symbol: str) -> str:
    return stooq_symbol.upper().removesuffix(".US")


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_quotes_csv(text: str) -> list[Quote]:
    """Parse /q/l/ CSV: Symbol,Date,Time,Open,High,Low,Close,Volume.

    Rows with 'N/D' (no data) closes are skipped.
    """
    quotes: list[Quote] = []
    for row in csv.DictReader(io.StringIO(text)):
        close = _parse_float(row.get("Close", ""))
        if close is None:
            continue
        try:
            day = date.fromisoformat(row["Date"])
            clock = dtime.fromisoformat(row.get("Time") or "00:00:00")
        except (KeyError, ValueError):
            continue
        quotes.append(
            Quote(
                symbol=from_stooq_symbol(row["Symbol"]),
                ts=datetime.combine(day, clock, tzinfo=UTC),
                open=_parse_float(row.get("Open", "")),
                high=_parse_float(row.get("High", "")),
                low=_parse_float(row.get("Low", "")),
                close=close,
                volume=_parse_float(row.get("Volume", "")),
            )
        )
    return quotes


def parse_history_csv(text: str) -> list[Bar]:
    """Parse /q/d/l/ CSV: Date,Open,High,Low,Close,Volume (oldest first)."""
    bars: list[Bar] = []
    for row in csv.DictReader(io.StringIO(text)):
        close = _parse_float(row.get("Close", ""))
        if close is None:
            continue
        try:
            day = date.fromisoformat(row["Date"])
        except (KeyError, ValueError):
            continue
        bars.append(
            Bar(
                ts=datetime.combine(day, dtime(0, 0), tzinfo=UTC),
                open=_parse_float(row.get("Open", "")),
                high=_parse_float(row.get("High", "")),
                low=_parse_float(row.get("Low", "")),
                close=close,
                volume=_parse_float(row.get("Volume", "")),
            )
        )
    return bars


def fetch_quotes(symbols: list[str]) -> list[Quote]:
    """Fetch latest quotes for our symbols, batched."""
    quotes: list[Quote] = []
    with httpx.Client(timeout=settings.provider_timeout_seconds) as client:
        for i in range(0, len(symbols), QUOTE_BATCH_SIZE):
            batch = symbols[i : i + QUOTE_BATCH_SIZE]
            joined = "+".join(to_stooq_symbol(s) for s in batch)
            res = client.get(
                f"{settings.stooq_base_url}/q/l/",
                params={"s": joined, "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            )
            res.raise_for_status()
            quotes.extend(parse_quotes_csv(res.text))
    return quotes


def fetch_daily_history(symbol: str) -> list[Bar]:
    """Fetch full daily OHLCV history for one symbol."""
    with httpx.Client(timeout=settings.provider_timeout_seconds) as client:
        res = client.get(
            f"{settings.stooq_base_url}/q/d/l/",
            params={"s": to_stooq_symbol(symbol), "i": "d"},
        )
        res.raise_for_status()
        return parse_history_csv(res.text)
