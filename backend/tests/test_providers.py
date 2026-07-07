"""Provider parsing tests against recorded response shapes (no network)."""

from datetime import UTC, datetime

from app.providers import coingecko, stooq

STOOQ_QUOTES_CSV = """Symbol,Date,Time,Open,High,Low,Close,Volume
AAPL.US,2026-07-06,22:00:11,210.11,213.5,209.8,212.44,48123456
BRK-B.US,2026-07-06,22:00:11,455.2,460.0,454.1,458.75,3456789
FAKE.US,N/D,N/D,N/D,N/D,N/D,N/D,N/D
"""

STOOQ_HISTORY_CSV = """Date,Open,High,Low,Close,Volume
2026-07-02,208.5,210.2,207.9,209.3,41234567
2026-07-03,209.4,211.0,208.8,210.6,39876543
2026-07-06,210.11,213.5,209.8,212.44,48123456
"""

COINGECKO_MARKETS = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 97214.0,
        "market_cap": 1923456789012,
        "price_change_percentage_24h": 1.92,
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "current_price": 3412.5,
        "market_cap": 410987654321,
        "price_change_percentage_24h": -0.88,
    },
    {"id": "broken", "symbol": "brk", "current_price": None},
]

COINGECKO_CHART = {
    "prices": [[1751500800000, 96000.5], [1751587200000, 97214.0]],
    "total_volumes": [[1751500800000, 3.2e10], [1751587200000, 2.9e10]],
}


def test_stooq_symbol_mapping():
    assert stooq.to_stooq_symbol("AAPL") == "aapl.us"
    assert stooq.to_stooq_symbol("BRK-B") == "brk-b.us"
    assert stooq.to_stooq_symbol("BRK.B") == "brk-b.us"
    assert stooq.from_stooq_symbol("AAPL.US") == "AAPL"
    assert stooq.from_stooq_symbol("brk-b.us") == "BRK-B"


def test_stooq_quote_parsing_skips_no_data_rows():
    quotes = stooq.parse_quotes_csv(STOOQ_QUOTES_CSV)
    assert [q.symbol for q in quotes] == ["AAPL", "BRK-B"]
    aapl = quotes[0]
    assert aapl.close == 212.44
    assert aapl.volume == 48123456
    assert aapl.ts == datetime(2026, 7, 6, 22, 0, 11, tzinfo=UTC)


def test_stooq_history_parsing():
    bars = stooq.parse_history_csv(STOOQ_HISTORY_CSV)
    assert len(bars) == 3
    assert bars[0].ts < bars[-1].ts
    assert bars[-1].close == 212.44
    assert bars[0].open == 208.5


def test_coingecko_markets_parsing_skips_null_prices():
    markets = coingecko.parse_markets(COINGECKO_MARKETS)
    assert [m.coingecko_id for m in markets] == ["bitcoin", "ethereum"]
    assert markets[0].price == 97214.0
    assert markets[0].day_change_pct == 1.92
    assert markets[1].market_cap == 410987654321


def test_coingecko_chart_parsing_joins_volumes():
    points = coingecko.parse_market_chart(COINGECKO_CHART)
    assert len(points) == 2
    assert points[1].price == 97214.0
    assert points[1].volume == 2.9e10
    assert points[0].ts.tzinfo is not None
