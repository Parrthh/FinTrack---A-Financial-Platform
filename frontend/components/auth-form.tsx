"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const { login, signup } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "signup") {
        await signup(email, password, displayName);
      } else {
        await login(email, password);
      }
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm " +
    "placeholder-slate-500 focus:border-emerald-400 focus:outline-none";

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 block text-center text-2xl font-bold">
          Fin<span className="text-emerald-400">Track</span>
        </Link>
        <h1 className="mb-6 text-center text-xl font-semibold">
          {mode === "signup" ? "Create your account" : "Welcome back"}
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "signup" && (
            <input
              className={inputClass}
              placeholder="Display name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              maxLength={100}
            />
          )}
          <input
            className={inputClass}
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <input
            className={inputClass}
            type="password"
            placeholder={mode === "signup" ? "Password (min 8 characters)" : "Password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={mode === "signup" ? 8 : 1}
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
          />
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-emerald-500 py-2 font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {submitting ? "Please wait…" : mode === "signup" ? "Sign up" : "Log in"}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-400">
          {mode === "signup" ? (
            <>
              Already have an account?{" "}
              <Link href="/login" className="text-emerald-400 hover:underline">
                Log in
              </Link>
            </>
          ) : (
            <>
              New to FinTrack?{" "}
              <Link href="/signup" className="text-emerald-400 hover:underline">
                Create an account
              </Link>
            </>
          )}
        </p>
      </div>
    </main>
  );
}
