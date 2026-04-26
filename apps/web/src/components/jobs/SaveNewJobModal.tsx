"use client";

import React, { useEffect, useRef, useState } from "react";
import { createJob, type JobRecord } from "@/lib/api/jobs";

interface SaveNewJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: (job: JobRecord) => void;
}

export default function SaveNewJobModal({ isOpen, onClose, onSaved }: SaveNewJobModalProps) {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTitle("");
      setCompany("");
      setDescription("");
      setError("");
      setTimeout(() => titleRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!title.trim() || !company.trim() || !description.trim()) {
      setError("Role, Company, and Job Description are required.");
      return;
    }

    setError("");
    setSaving(true);
    try {
      const saved = await createJob({
        title: title.trim(),
        company: company.trim(),
        description: description.trim(),
      });
      onSaved(saved);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to save job.");
    } finally {
      setSaving(false);
    }
  };

  return (
    // Panel floats centered — no overlay, no backdrop, page behind stays fully interactive.
    <div
      className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-11/12 max-w-md bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden"
      style={{ animation: "modal-pop 180ms cubic-bezier(0.34, 1.3, 0.64, 1) forwards" }}
      aria-modal="true"
      role="dialog"
    >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h3 className="font-display font-bold text-lg text-slate-900">Save New Job</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 flex flex-col gap-4">
          {error && (
            <p className="text-sm text-[var(--warning)] bg-[var(--warning-soft)] px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] ml-1">Role</label>
            <input
              ref={titleRef}
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="h-10 px-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none text-sm"
              placeholder="e.g. Senior Backend Engineer"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] ml-1">Company</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="h-10 px-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none text-sm"
              placeholder="e.g. Acme Corp"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] ml-1">Job Description</label>
            <textarea
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none text-sm leading-relaxed resize-none bg-slate-50"
              placeholder="Paste the job description here..."
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex gap-3">
          <button type="button" onClick={onClose} className="cta-ghost flex-1">
            Cancel
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="cta-main flex-1"
          >
            {saving ? "Saving..." : "Save Job"}
          </button>
        </div>
      </div>
  );
}

