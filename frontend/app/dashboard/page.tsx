"use client";

/**
 * Dashboard shell (Phase 1). The placeholder panels below get real content in
 * later phases: watchlists (Phase 3), progress news (Phase 4), live prices
 * (Phases 2/5).
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth-context";

const PANELS = [
  {
    title: "Watchlist",
    body: "Your followed assets and their latest prices will appear here.",
    phase: "Phase 3",
  },
  {
    title: "Progress news",
    body: "Daily news flagged as genuine company progress for assets you follow.",
    phase: "Phase 4",
  },
  {
    title: "Market movers",
    body: "Top movers across stocks, ETFs, and crypto.",
    phase: "Phase 2",
  },
];

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center text-slate-500">
        Loading…
      </main>
    );
  }

  return (
    <main className="flex-1">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-bold">
            Fin<span className="text-emerald-400">Track</span>
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-400">{user.display_name}</span>
            <button
              // Clearing the user trips the auth guard above, which redirects
              // to /login — no explicit navigation needed here.
              onClick={() => logout()}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-slate-300 hover:border-slate-500"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <h1 className="text-2xl font-semibold">
          Welcome, {user.display_name}
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Your dashboard is ready — market data, watchlists, and news
          intelligence land in the upcoming phases.
        </p>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {PANELS.map((p) => (
            <div
              key={p.title}
              className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 p-6"
            >
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-200">{p.title}</h2>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                  {p.phase}
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-500">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
