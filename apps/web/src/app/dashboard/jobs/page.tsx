"use client";

import React, { useState } from "react";
import { createJob } from "@/lib/api/jobs";

export default function JobsPage() {
  const [role, setRole] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSaveJob = async () => {
    if (!role.trim() || !companyName.trim() || !jobDescription.trim()) {
      setSuccess("");
      setError("Role, Company Name, and Job Description are required.");
      return;
    }

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      await createJob({
        title: role.trim(),
        company: companyName.trim(),
        description: jobDescription.trim(),
      });
      setSuccess("Job saved successfully.");
      setRole("");
      setCompanyName("");
      setJobDescription("");
    } catch (err: any) {
      setError(err.message || "Failed to save job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-rise flex justify-center">
      <div className="w-full max-w-2xl">
        <div className="mb-8 text-center">
          <h2 className="font-display text-3xl font-bold text-slate-900">Jobs</h2>
          <p className="text-slate-600 mt-2">Save a job for use across resume generation, outreach, and answers.</p>
        </div>

        {error && (
          <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-6 font-medium">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-[var(--accent-soft)] text-[var(--accent)] p-4 rounded-xl mb-6 font-medium">
            {success}
          </div>
        )}

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex flex-col gap-2 mb-5">
            <label className="text-sm font-semibold text-[var(--accent)]">Role</label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="h-12 px-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none"
              placeholder="e.g. Senior Backend Engineer"
            />
          </div>

          <div className="flex flex-col gap-2 mb-5">
            <label className="text-sm font-semibold text-[var(--accent)]">Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="h-12 px-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none"
              placeholder="e.g. Acme Corp"
            />
          </div>

          <div className="flex flex-col gap-2 mb-6">
            <label className="text-sm font-semibold text-[var(--accent)]">Job Description</label>
            <textarea
              rows={10}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none resize-y text-sm leading-relaxed bg-slate-50"
              placeholder="Paste the target job description here..."
            />
          </div>

          <button
            onClick={handleSaveJob}
            disabled={loading}
            className="cta-main w-full flex justify-center"
          >
            {loading ? "Saving..." : "Save Job"}
          </button>
        </div>
      </div>
    </div>
  );
}
