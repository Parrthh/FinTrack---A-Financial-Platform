"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, type AssetList } from "@/lib/api";
import {
  ASSET_TYPE_LABELS,
  changeClass,
  formatChange,
  formatMarketCap,
  formatPrice,
} from "@/lib/format";
import { SiteHeader } from "@/components/site-header";

const TYPE_TABS = [
  { value: "", label: "All" },
  { value: "stock", label: "Stocks" },
  { value: "etf", label: "ETFs" },
  { value: "crypto", label: "Crypto" },
];

const PAGE_SIZE = 50;

export default function AssetsPage() {
  const [q, setQ] = useState("");
  const [assetType, setAssetType] = useState("");
  const [sort, setSort] = useState<{ key: string; order: "asc" | "desc" }>({
    key: "symbol",
    order: "asc",
  });
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<AssetList | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(
      () => {
        api
          .listAssets({
            q,
            asset_type: assetType,
            sort: sort.key,
            order: sort.order,
            limit: PAGE_SIZE,
            offset,
          })
          .then((res) => {
            if (!cancelled) {
              setData(res);
              setError(null);
            }
          })
          .catch(() => {
            if (!cancelled) setError("Could not load assets. Is the API running?");
          });
      },
      q ? 250 : 0, // debounce typing, fetch immediately otherwise
    );
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [q, assetType, sort, offset]);

  function toggleSort(key: string) {
    setOffset(0);
    setSort((prev) =>
      prev.key === key
        ? { key, order: prev.order === "asc" ? "desc" : "asc" }
        : { key, order: key === "symbol" || key === "name" ? "asc" : "desc" },
    );
  }

  function sortIndicator(key: string) {
    if (sort.key !== key) return "";
    return sort.order === "asc" ? " ↑" : " ↓";
  }

  const headers: { key: string; label: string; align: string }[] = [
    { key: "symbol", label: "Symbol", align: "text-left" },
    { key: "name", label: "Name", align: "text-left" },
    { key: "price", label: "Price", align: "text-right" },
    { key: "change", label: "Day %", align: "text-right" },
    { key: "market_cap", label: "Mkt Cap", align: "text-right" },
  ];

  return (
    <main className="flex-1">
      <SiteHeader />
      <div className="mx-auto w-full max-w-6xl px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold">Markets</h1>
          <p className="text-xs text-slate-500">
            Stock/ETF quotes are delayed (free data); crypto is near-real-time.
          </p>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setOffset(0);
            }}
            placeholder="Search symbol or name…"
            className="w-64 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm placeholder-slate-500 focus:border-emerald-400 focus:outline-none"
          />
          <div className="flex rounded-md border border-slate-700 text-sm">
            {TYPE_TABS.map((tab) => (
              <button
                key={tab.value}
                onClick={() => {
                  setAssetType(tab.value);
                  setOffset(0);
                }}
                className={`px-4 py-2 first:rounded-l-md last:rounded-r-md ${
                  assetType === tab.value
                    ? "bg-emerald-500 font-semibold text-slate-950"
                    : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="mt-8 text-sm text-rose-400">{error}</p>}

        <div className="mt-6 overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                {headers.map((h) => (
                  <th key={h.key} className={`px-4 py-3 ${h.align}`}>
                    <button onClick={() => toggleSort(h.key)} className="hover:text-white">
                      {h.label}
                      {sortIndicator(h.key)}
                    </button>
                  </th>
                ))}
                <th className="px-4 py-3 text-right">Type</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((a) => (
                <tr key={a.id} className="border-t border-slate-800/60 hover:bg-slate-900/50">
                  <td className="px-4 py-3 font-mono font-semibold">
                    <Link href={`/assets/${a.symbol}`} className="text-emerald-300 hover:underline">
                      {a.symbol}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{a.name}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatPrice(a.last_price)}</td>
                  <td className={`px-4 py-3 text-right font-mono ${changeClass(a.day_change_pct)}`}>
                    {formatChange(a.day_change_pct)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-400">
                    {formatMarketCap(a.market_cap)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                      {ASSET_TYPE_LABELS[a.asset_type]}
                    </span>
                  </td>
                </tr>
              ))}
              {data && data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                    No assets match your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data && data.total > PAGE_SIZE && (
          <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
            <span>
              Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
            </span>
            <div className="flex gap-2">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded border border-slate-700 px-3 py-1.5 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={offset + PAGE_SIZE >= data.total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded border border-slate-700 px-3 py-1.5 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
