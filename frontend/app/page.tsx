import Link from "next/link";

import { TickerStrip } from "@/components/ticker-strip";

const FEATURES = [
  {
    title: "One universe, three asset classes",
    body: "Search and follow stocks, ETFs, and crypto side by side, with key stats and price history in one place.",
  },
  {
    title: "News that signals progress",
    body: "Daily-scraped financial news, deduplicated and tagged to companies — with a clear flag when a story is genuine progress (launches, earnings beats, partnerships), plus the reasoning why.",
  },
  {
    title: "Your dashboard, your watchlists",
    body: "Build watchlists, track the movers you care about, and get a morning snapshot of flagged progress news for the companies you follow.",
  },
  {
    title: "Honest about freshness",
    body: "Crypto prices stream near-real-time; stock quotes are ~15-minute delayed (free data, clearly labeled). No fake real-time claims.",
  },
];

export default function LandingPage() {
  return (
    <main className="flex-1">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <span className="text-xl font-bold tracking-tight">
          Fin<span className="text-emerald-400">Track</span>
        </span>
        <nav className="flex items-center gap-3">
          <Link
            href="/assets"
            className="rounded-md px-4 py-2 text-sm text-slate-300 hover:text-white"
          >
            Markets
          </Link>
          <Link
            href="/login"
            className="rounded-md px-4 py-2 text-sm text-slate-300 hover:text-white"
          >
            Log in
          </Link>
          <Link
            href="/signup"
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400"
          >
            Get started
          </Link>
        </nav>
      </header>

      <TickerStrip />

      <section className="mx-auto max-w-6xl px-6 py-20 text-center">
        <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight sm:text-5xl">
          Market intelligence that tells you{" "}
          <span className="text-emerald-400">which companies are actually moving forward</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
          FinTrack aggregates prices for stocks, ETFs, and crypto, scrapes the
          day&apos;s financial news, and flags the stories that signal real company
          progress — so your watchlist tells you more than just price.
        </p>
        <div className="mt-10 flex justify-center gap-4">
          <Link
            href="/signup"
            className="rounded-md bg-emerald-500 px-6 py-3 font-semibold text-slate-950 hover:bg-emerald-400"
          >
            Create a free account
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-slate-700 px-6 py-3 font-semibold text-slate-200 hover:border-slate-500"
          >
            Log in
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 pb-24 sm:grid-cols-2">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-lg border border-slate-800 bg-slate-900/50 p-6"
          >
            <h2 className="text-lg font-semibold text-emerald-300">{f.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.body}</p>
          </div>
        ))}
      </section>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-600">
        FinTrack is a read-only market intelligence tool — not a broker, and not
        investment advice.
      </footer>
    </main>
  );
}
