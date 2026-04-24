"use client";

import React, { useEffect, useState } from "react";
import { listJobs, type JobRecord } from "@/lib/api/jobs";
import { generateCoverLetter, generateColdEmail } from "@/lib/api/outreach";

export default function OutreachPage() {
  const [savedJobs, setSavedJobs] = useState<JobRecord[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [companyContext, setCompanyContext] = useState("");
  
  const [loading, setLoading] = useState<"cover-letter" | "cold-email" | null>(null);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const loadJobs = async () => {
      setJobsLoading(true);
      try {
        const jobs = await listJobs();
        setSavedJobs(jobs);
      } catch {
        // Job selection is optional here, so keep generation available with manual entry.
      } finally {
        setJobsLoading(false);
      }
    };

    void loadJobs();
  }, []);

  const applySelectedJob = (jobId: string) => {
    setSelectedJobId(jobId);
    const selectedJob = savedJobs.find((job) => job.id === jobId);
    if (!selectedJob) {
      return;
    }

    setJobTitle(selectedJob.title);
    setCompany(selectedJob.company);
    setJobDescription(selectedJob.description || "");
  };

  const handleGenerate = async (type: "cover-letter" | "cold-email") => {
    if (!jobTitle || !company || !jobDescription) {
      setError("Title, Company, and Description are required.");
      return;
    }
    
    setError("");
    setResult("");
    setLoading(type);

    try {
      if (type === "cover-letter") {
        const resp = await generateCoverLetter({ job_title: jobTitle, company, job_description: jobDescription, company_context: companyContext });
        setResult(resp.cover_letter);
      } else {
        const resp = await generateColdEmail({ job_title: jobTitle, company, job_description: jobDescription, company_context: companyContext });
        setResult(`Subject: ${resp.subject}\n\n${resp.message}`);
      }
    } catch (err: any) {
      setError(err.message || `Failed to generate ${type}.`);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="animate-rise">
      <div className="mb-8">
        <h2 className="font-display text-3xl font-bold text-slate-900">Outreach Studio</h2>
        <p className="text-slate-600 mt-2">Generate hyper-personalized cover letters and recruiter outreach messages.</p>
      </div>

      {error && (
        <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-8 font-medium">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col gap-5">
          <h3 className="font-bold font-display text-lg mb-2">Job Context</h3>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-700">Select Saved Job (Optional)</label>
            <select
              value={selectedJobId}
              onChange={(e) => applySelectedJob(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none text-sm bg-white"
            >
              <option value="">{jobsLoading ? "Loading saved jobs..." : "Select a saved job"}</option>
              {savedJobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} at {job.company}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-700">Job Title</label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none"
              placeholder="e.g. Senior Frontend Engineer"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-700">Company</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none"
              placeholder="e.g. Acme Corp"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-700">Job Description</label>
            <textarea
              rows={4}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none resize-y text-sm bg-slate-50"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-700">Company Context (Optional)</label>
            <input
              type="text"
              value={companyContext}
              onChange={(e) => setCompanyContext(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none text-sm"
              placeholder="e.g. They recently raised Series B"
            />
          </div>

          <div className="flex gap-4 mt-2">
            <button 
              onClick={() => handleGenerate("cover-letter")} 
              disabled={loading !== null} 
              className="cta-main flex-1 flex justify-center"
            >
              {loading === "cover-letter" ? "Generating..." : "Cover Letter"}
            </button>
            <button 
              onClick={() => handleGenerate("cold-email")} 
              disabled={loading !== null} 
              className="cta-ghost flex-1 flex justify-center"
            >
              {loading === "cold-email" ? "Generating..." : "Cold Email"}
            </button>
          </div>
        </div>

        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold font-display text-lg">Generated Output</h3>
            {result && (
              <button 
                onClick={() => navigator.clipboard.writeText(result)}
                className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] hover:underline"
              >
                Copy Text
              </button>
            )}
          </div>
          
          {result ? (
            <div className="bg-white p-4 rounded-xl border border-slate-200 flex-1 overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-serif">
              {result}
            </div>
          ) : (
            <div className="flex-1 flex flex-col justify-center items-center text-center opacity-50">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              <p className="text-sm font-medium">Output will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
