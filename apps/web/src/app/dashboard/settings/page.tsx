"use client";

import React, { useState } from "react";
import { changePassword } from "@/lib/api/auth";

export default function SettingsPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);

    if (newPassword.length < 8) {
      setMessage({ type: "error", text: "New password must be at least 8 characters long." });
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage({ type: "error", text: "New password and confirm password must match." });
      return;
    }

    if (currentPassword === newPassword) {
      setMessage({ type: "error", text: "New password must be different from current password." });
      return;
    }

    setLoading(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage({ type: "success", text: "Password changed successfully." });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to change password.";
      setMessage({ type: "error", text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-rise max-w-2xl mx-auto">
      <div className="mb-8">
        <h2 className="font-display text-3xl font-bold text-slate-900">Change Password</h2>
        <p className="text-slate-600 mt-2">Manage your account security settings.</p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl mb-6 font-medium ${
            message.type === "error"
              ? "bg-[var(--warning-soft)] text-[var(--warning)]"
              : "bg-[var(--accent-soft)] text-[var(--accent)]"
          }`}
        >
          {message.text}
        </div>
      )}

      <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h3 className="font-bold font-display text-lg text-slate-900 mb-1">Change Password</h3>
        <p className="text-sm text-slate-500 mb-6">Use a strong password you do not reuse on other websites.</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-[var(--accent)]" htmlFor="current-password">
              Current Password
            </label>
            <input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              required
              minLength={8}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none transition bg-white"
              placeholder="Enter current password"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-[var(--accent)]" htmlFor="new-password">
              New Password
            </label>
            <input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              required
              minLength={8}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none transition bg-white"
              placeholder="Enter new password"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-[var(--accent)]" htmlFor="confirm-password">
              Confirm New Password
            </label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
              minLength={8}
              className="p-2.5 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none transition bg-white"
              placeholder="Re-enter new password"
            />
          </div>

          <button type="submit" disabled={loading} className="cta-main w-full mt-2 disabled:opacity-70">
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>
      </section>
    </div>
  );
}