"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { register } from "@/lib/api/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await register({ name, email, password });
      setUser(response.user);
      router.push("/onboarding");
    } catch (err: any) {
      setError(err.message || "Failed to register account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell flex items-center justify-center px-6">
      <div className="w-full max-w-md bg-[var(--panel)] p-8 rounded-2xl shadow-sm border border-slate-200 animate-rise" style={{ animationDelay: "50ms" }}>
        <h1 className="font-display text-3xl font-bold text-slate-900 mb-2">Join Widenet</h1>
        <p className="text-slate-600 mb-8">Create your platform account.</p>

        {error && (
          <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-3 rounded-xl mb-6 text-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-700" htmlFor="name">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none transition"
              placeholder="Jane Doe"
            />
          </div>

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
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none transition"
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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none transition"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="cta-main w-full mt-2 flex justify-center disabled:opacity-70"
          >
            {loading ? "Creating..." : "Create Account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-slate-600">
          Already have an account?{" "}
          <button onClick={() => router.push("/login")} className="text-[var(--accent)] font-bold hover:underline">
            Sign In here
          </button>
        </p>
      </div>
    </main>
  );
}
