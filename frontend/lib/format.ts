export function formatPrice(value: number | null): string {
  if (value === null) return "—";
  if (value >= 1000) {
    return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }
  return value.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: value < 1 ? 4 : 2,
  });
}

export function formatChange(pct: number | null): string {
  if (pct === null) return "—";
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

export function changeClass(pct: number | null): string {
  if (pct === null) return "text-slate-500";
  return pct >= 0 ? "text-emerald-400" : "text-rose-400";
}

export function formatMarketCap(value: number | null): string {
  if (value === null) return "—";
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export const ASSET_TYPE_LABELS: Record<string, string> = {
  stock: "Stock",
  etf: "ETF",
  crypto: "Crypto",
};
