"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { login } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await login({ email, password });
      setUser(response.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to log in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell flex items-center justify-center px-6">
      <div className="w-full max-w-md bg-[var(--panel)] p-8 rounded-2xl shadow-sm border border-slate-200 animate-rise">
        <h1 className="font-display text-3xl font-bold text-slate-900 mb-2">Welcome back</h1>
        <p className="text-slate-600 mb-8">Sign in to your Widenet account.</p>

        {error && (
          <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-3 rounded-xl mb-6 text-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-700" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none transition transition-shadow bg-white"
              placeholder="you@example.com"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-700" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none transition bg-white"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="cta-main w-full mt-2 disabled:opacity-70 flex items-center justify-center"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-slate-600">
          Don't have an account?{" "}
          <button onClick={() => router.push("/register")} className="text-[var(--accent)] font-bold hover:underline">
            Register here
          </button>
        </p>
      </div>
    </main>
  );
}
