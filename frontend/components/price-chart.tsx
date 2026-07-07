"use client";

import { AreaSeries, ColorType, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { PriceBar } from "@/lib/api";

export function PriceChart({ bars }: { bars: PriceBar[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || bars.length === 0) return;

    const chart = createChart(container, {
      height: 380,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      timeScale: { borderColor: "#334155" },
      rightPriceScale: { borderColor: "#334155" },
    });

    const first = bars[0]?.close ?? 0;
    const last = bars[bars.length - 1]?.close ?? 0;
    const up = last >= first;
    const series = chart.addSeries(AreaSeries, {
      lineColor: up ? "#34d399" : "#fb7185",
      topColor: up ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 113, 133, 0.3)",
      bottomColor: "rgba(0, 0, 0, 0)",
      lineWidth: 2,
    });
    series.setData(
      bars
        .filter((b) => b.close !== null)
        .map((b) => ({ time: b.ts.slice(0, 10), value: b.close as number })),
    );
    chart.timeScale().fitContent();

    const observer = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [bars]);

  if (bars.length === 0) {
    return (
      <div className="flex h-[380px] items-center justify-center rounded-lg border border-slate-800 text-sm text-slate-500">
        No price history available yet.
      </div>
    );
  }
  return <div ref={containerRef} className="w-full" />;
}
