/**
 * Landing-page ticker strip. Static sample data for Phase 1 — gets wired to
 * the market-data service (cached quotes) in Phase 2. Values are illustrative
 * and labeled as such in the UI.
 */

const SAMPLE_TICKERS = [
  { symbol: "AAPL", price: "212.44", change: +0.82 },
  { symbol: "MSFT", price: "448.10", change: -0.31 },
  { symbol: "NVDA", price: "131.26", change: +2.14 },
  { symbol: "SPY", price: "552.08", change: +0.45 },
  { symbol: "QQQ", price: "485.92", change: +0.67 },
  { symbol: "BTC", price: "97,214", change: +1.92 },
  { symbol: "ETH", price: "3,412", change: -0.88 },
  { symbol: "AMZN", price: "186.33", change: +0.29 },
  { symbol: "GOOGL", price: "176.51", change: -0.12 },
  { symbol: "TSLA", price: "241.05", change: +1.37 },
];

export function TickerStrip() {
  return (
    <div className="w-full overflow-hidden border-y border-slate-800 bg-slate-900/60 py-2">
      <div className="flex flex-wrap justify-center gap-x-8 gap-y-1 px-4 font-mono text-sm">
        {SAMPLE_TICKERS.map((t) => (
          <span key={t.symbol} className="whitespace-nowrap">
            <span className="text-slate-300">{t.symbol}</span>{" "}
            <span className="text-slate-400">{t.price}</span>{" "}
            <span className={t.change >= 0 ? "text-emerald-400" : "text-rose-400"}>
              {t.change >= 0 ? "▲" : "▼"} {Math.abs(t.change).toFixed(2)}%
            </span>
          </span>
        ))}
      </div>
      <p className="mt-1 text-center text-[10px] uppercase tracking-wide text-slate-600">
        Sample data — live quotes (delayed ~15 min for stocks) arrive in Phase 2
      </p>
    </div>
  );
}
