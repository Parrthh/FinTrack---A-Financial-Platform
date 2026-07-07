"use client";

/**
 * Landing-page ticker strip. Fetches top movers from the API; falls back to
 * labeled sample data when the API is unreachable (e.g. cold start).
 */

import { useEffect, useState } from "react";

import { api, type TickerEntry } from "@/lib/api";
import { changeClass, formatPrice } from "@/lib/format";

const SAMPLE_TICKERS: TickerEntry[] = [
  { symbol: "AAPL", asset_type: "stock", last_price: 212.44, day_change_pct: 0.82 },
  { symbol: "MSFT", asset_type: "stock", last_price: 448.1, day_change_pct: -0.31 },
  { symbol: "NVDA", asset_type: "stock", last_price: 131.26, day_change_pct: 2.14 },
  { symbol: "SPY", asset_type: "etf", last_price: 552.08, day_change_pct: 0.45 },
  { symbol: "QQQ", asset_type: "etf", last_price: 485.92, day_change_pct: 0.67 },
  { symbol: "BTC", asset_type: "crypto", last_price: 97214, day_change_pct: 1.92 },
  { symbol: "ETH", asset_type: "crypto", last_price: 3412, day_change_pct: -0.88 },
  { symbol: "AMZN", asset_type: "stock", last_price: 186.33, day_change_pct: 0.29 },
];

export function TickerStrip() {
  const [tickers, setTickers] = useState<TickerEntry[]>([]);
  const [live, setLive] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .marketTicker(10)
      .then((entries) => {
        if (!cancelled && entries.length > 0) {
          setTickers(entries);
          setLive(true);
        } else if (!cancelled) {
          setTickers(SAMPLE_TICKERS);
        }
      })
      .catch(() => {
        if (!cancelled) setTickers(SAMPLE_TICKERS);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (tickers.length === 0) {
    return <div className="h-[62px] border-y border-slate-800 bg-slate-900/60" />;
  }

  return (
    <div className="w-full overflow-hidden border-y border-slate-800 bg-slate-900/60 py-2">
      <div className="flex flex-wrap justify-center gap-x-8 gap-y-1 px-4 font-mono text-sm">
        {tickers.map((t) => (
          <span key={t.symbol} className="whitespace-nowrap">
            <span className="text-slate-300">{t.symbol}</span>{" "}
            <span className="text-slate-400">{formatPrice(t.last_price)}</span>{" "}
            <span className={changeClass(t.day_change_pct)}>
              {t.day_change_pct !== null && t.day_change_pct >= 0 ? "▲" : "▼"}{" "}
              {Math.abs(t.day_change_pct ?? 0).toFixed(2)}%
            </span>
          </span>
        ))}
      </div>
      <p className="mt-1 text-center text-[10px] uppercase tracking-wide text-slate-600">
        {live
          ? "Top movers — stock/ETF quotes delayed (free data); crypto near-real-time"
          : "Sample data — connect the API for live quotes"}
      </p>
    </div>
  );
}
