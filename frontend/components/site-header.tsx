"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

export function SiteHeader() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="border-b border-slate-800">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-lg font-bold">
            Fin<span className="text-emerald-400">Track</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm text-slate-300">
            <Link href="/assets" className="hover:text-white">
              Markets
            </Link>
            {user && (
              <Link href="/dashboard" className="hover:text-white">
                Dashboard
              </Link>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {loading ? null : user ? (
            <>
              <span className="text-slate-400">{user.display_name}</span>
              <button
                onClick={async () => {
                  await logout();
                  router.push("/");
                }}
                className="rounded-md border border-slate-700 px-3 py-1.5 text-slate-300 hover:border-slate-500"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-slate-300 hover:text-white">
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-md bg-emerald-500 px-3 py-1.5 font-semibold text-slate-950 hover:bg-emerald-400"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
