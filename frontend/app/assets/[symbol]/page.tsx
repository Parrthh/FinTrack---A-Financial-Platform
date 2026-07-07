"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { api, type Asset, type AssetHistory } from "@/lib/api";
import { SiteHeader } from "@/components/site-header";
import { PriceChart } from "@/components/price-chart";
import {
  ASSET_TYPE_LABELS,
  changeClass,
  formatChange,
  formatMarketCap,
  formatPrice,
} from "@/lib/format";

const RANGES = ["1m", "3m", "6m", "1y", "2y", "max"] as const;

export default function AssetDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = params.symbol?.toUpperCase() ?? "";
  const [asset, setAsset] = useState<Asset | null>(null);
  const [history, setHistory] = useState<AssetHistory | null>(null);
  const [range, setRange] = useState<(typeof RANGES)[number]>("1y");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    api
      .getAsset(symbol)
      .then(setAsset)
      .catch(() => setError(`Asset "${symbol}" not found.`));
  }, [symbol]);

  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;
    api
      .getAssetHistory(symbol, range)
      .then((h) => {
        if (!cancelled) setHistory(h);
      })
      .catch(() => {
        if (!cancelled) setHistory(null);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, range]);

  if (error) {
    return (
      <main className="flex-1">
        <SiteHeader />
        <div className="mx-auto max-w-6xl px-6 py-16 text-center">
          <p className="text-slate-400">{error}</p>
          <Link href="/assets" className="mt-4 inline-block text-emerald-400 hover:underline">
            ← Back to markets
          </Link>
        </div>
      </main>
    );
  }

  const stats: { label: string; value: string }[] = asset
    ? [
        { label: "Type", value: ASSET_TYPE_LABELS[asset.asset_type] },
        { label: "Exchange", value: asset.exchange ?? "—" },
        { label: "Sector", value: asset.sector ?? "—" },
        { label: "Currency", value: asset.currency },
        { label: "Market cap", value: formatMarketCap(asset.market_cap) },
        {
          label: "Last updated",
          value: asset.last_price_at
            ? new Date(asset.last_price_at + "Z").toLocaleString()
            : "—",
        },
      ]
    : [];

  return (
    <main className="flex-1">
      <SiteHeader />
      <div className="mx-auto w-full max-w-6xl px-6 py-8">
        <Link href="/assets" className="text-sm text-slate-400 hover:text-white">
          ← Markets
        </Link>

        {asset && (
          <>
            <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold">
                  <span className="font-mono">{asset.symbol}</span>{" "}
                  <span className="text-xl font-normal text-slate-400">{asset.name}</span>
                </h1>
                <div className="mt-2 flex items-baseline gap-3">
                  <span className="font-mono text-3xl">{formatPrice(asset.last_price)}</span>
                  <span className={`font-mono text-lg ${changeClass(asset.day_change_pct)}`}>
                    {formatChange(asset.day_change_pct)}
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-500">
                {asset.asset_type === "crypto"
                  ? "Crypto prices are near-real-time (CoinGecko)."
                  : "Prices are end-of-day/delayed — free data feed (Stooq)."}
              </p>
            </div>

            <div className="mt-6 flex gap-1">
              {RANGES.map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`rounded px-3 py-1 text-xs font-semibold uppercase ${
                    range === r
                      ? "bg-emerald-500 text-slate-950"
                      : "text-slate-400 hover:bg-slate-800"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="mt-4">
              <PriceChart bars={history?.bars ?? []} />
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-3">
              {stats.map((s) => (
                <div key={s.label} className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
                  <p className="text-xs uppercase tracking-wide text-slate-500">{s.label}</p>
                  <p className="mt-1 font-medium text-slate-200">{s.value}</p>
                </div>
              ))}
            </div>

            <div className="mt-8 rounded-lg border border-dashed border-slate-700 bg-slate-900/40 p-6">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-200">Related news</h2>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                  Phase 4
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-500">
                Daily-scraped news tagged to {asset.symbol}, with progress signals, lands here.
              </p>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
