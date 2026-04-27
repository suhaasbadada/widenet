"use client";

import React, { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { generateAnswer } from "@/lib/api/answers";
import { listJobs, type JobRecord } from "@/lib/api/jobs";
import { generateCoverLetter, generateColdEmail } from "@/lib/api/outreach";
import { generateAndRenderFile } from "@/lib/api/resumes";
import { useAuth } from "@/components/providers/AuthProvider";
import SaveNewJobModal from "@/components/jobs/SaveNewJobModal";

type StudioMode = "resume" | "outreach" | "answers";
type OutreachType = "cover-letter" | "cold-email";
type ResumeFormat = "pdf" | "docx";

type AnswerHistoryItem = {
  question: string;
  answer: string;
};

const modeOptions: Array<{ id: StudioMode; label: string; description: string }> = [
  {
    id: "resume",
    label: "Resume",
    description: "Create a tailored export for the selected role.",
  },
  {
    id: "outreach",
    label: "Outreach",
    description: "Generate recruiter-facing content from the same job.",
  },
  {
    id: "answers",
    label: "Answers",
    description: "Build reusable application responses for this job.",
  },
];

function normalizeMode(value: string | null): StudioMode {
  if (value === "resume" || value === "outreach" || value === "answers") {
    return value;
  }
  return "resume";
}

export default function StudioPage() {
  const { user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [activeMode, setActiveMode] = useState<StudioMode>(() => normalizeMode(searchParams.get("mode")));
  const [outreachType, setOutreachType] = useState<OutreachType>("cover-letter");
  const [savedJobs, setSavedJobs] = useState<JobRecord[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [jobsLoading, setJobsLoading] = useState(false);
  const [companyContext, setCompanyContext] = useState("");
  const [question, setQuestion] = useState("");
  const [answerHistory, setAnswerHistory] = useState<AnswerHistoryItem[]>([]);
  const [outreachResult, setOutreachResult] = useState("");
  const [resumeStatus, setResumeStatus] = useState("");
  const [loading, setLoading] = useState<StudioMode | null>(null);
  const [outreachLoading, setOutreachLoading] = useState<OutreachType | null>(null);
  const [resumeFormatLoading, setResumeFormatLoading] = useState<ResumeFormat | null>(null);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [saveModalAnchorRect, setSaveModalAnchorRect] = useState<DOMRect | null>(null);
  const [isJobDescriptionOpen, setIsJobDescriptionOpen] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setActiveMode(normalizeMode(searchParams.get("mode")));
  }, [searchParams]);

  useEffect(() => {
    const loadJobs = async () => {
      setJobsLoading(true);
      try {
        const jobs = await listJobs();
        setSavedJobs(jobs);
      } catch {
        // Keep the page usable even if saved jobs fail temporarily.
      } finally {
        setJobsLoading(false);
      }
    };

    void loadJobs();
  }, []);

  const selectedJob = useMemo(
    () => savedJobs.find((job) => job.id === selectedJobId) || null,
    [savedJobs, selectedJobId]
  );

  const updateMode = (mode: StudioMode) => {
    setActiveMode(mode);
    const params = new URLSearchParams(searchParams.toString());
    params.set("mode", mode);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const applySelectedJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setError("");
    setResumeStatus("");
    setIsJobDescriptionOpen(false);
  };

  const requireSelectedJob = (): JobRecord | null => {
    if (!selectedJob) {
      setError("Select a saved job or add a new one first.");
      return null;
    }

    if (!selectedJob.description?.trim()) {
      setError("The selected job does not have a description yet.");
      return null;
    }

    return selectedJob;
  };

  const handleNewJobSaved = (job: JobRecord) => {
    setSavedJobs((prev) => [job, ...prev]);
    setSelectedJobId(job.id);
    setIsJobDescriptionOpen(false);
    setError("");
  };

  const handleResumeGenerate = async (format: ResumeFormat) => {
    const job = requireSelectedJob();
    if (!job) {
      return;
    }

    const jobDescription = job.description ?? "";

    setError("");
    setResumeStatus("");
    setLoading("resume");
    setResumeFormatLoading(format);

    try {
      const blob = await generateAndRenderFile({
        job_description: jobDescription.trim(),
        output_format: format,
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `tailored_resume.${format}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setResumeStatus(`Tailored ${format.toUpperCase()} generated and downloaded.`);
    } catch (err: any) {
      setError(err.message || `Failed to generate tailored resume ${format.toUpperCase()}.`);
    } finally {
      setLoading(null);
      setResumeFormatLoading(null);
    }
  };

  const handleOutreachGenerate = async (type: OutreachType) => {
    const job = requireSelectedJob();
    if (!job) {
      return;
    }

    const jobDescription = job.description ?? "";

    setError("");
    setOutreachResult("");
    setOutreachLoading(type);

    try {
      if (type === "cover-letter") {
        const response = await generateCoverLetter({
          job_title: job.title,
          company: job.company,
          job_description: jobDescription,
          company_context: companyContext.trim(),
        });
        setOutreachResult(response.cover_letter);
      } else {
        const response = await generateColdEmail({
          job_title: job.title,
          company: job.company,
          job_description: jobDescription,
          company_context: companyContext.trim(),
        });
        setOutreachResult(`Subject: ${response.subject}\n\n${response.message}`);
      }
    } catch (err: any) {
      setError(err.message || `Failed to generate ${type}.`);
    } finally {
      setOutreachLoading(null);
    }
  };

  const handleAnswerGenerate = async () => {
    if (!question.trim() || question.trim().length < 5) {
      setError("Please ask a valid question.");
      return;
    }

    const job = requireSelectedJob();
    if (!job) {
      return;
    }

    setError("");
    setLoading("answers");

    try {
      const response = await generateAnswer({
        user_id: user?.id,
        job_id: job.id,
        question: question.trim(),
      });

      setAnswerHistory((prev) => [
        {
          question: question.trim(),
          answer: response.answer,
        },
        ...prev,
      ]);
      setQuestion("");
    } catch (err: any) {
      setError(err.message || "Failed to generate answer.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="animate-rise max-w-6xl mx-auto">
      <SaveNewJobModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        onSaved={handleNewJobSaved}
        anchorRect={saveModalAnchorRect}
      />

      <div className="mb-8 text-center">
        <h2 className="font-display text-3xl font-bold text-slate-900">Job Studio</h2>
      </div>

      {error && (
        <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-8 font-medium">
          {error}
        </div>
      )}

      <section className="bg-white p-5 md:p-6 rounded-[2rem] shadow-sm border border-slate-200 mb-8">
        <div className="max-w-4xl mx-auto">
          <p className="mb-3 pl-2 text-left text-[var(--accent)] text-sm md:text-base font-medium">
            Select an existing job to make it the active context, or tap the plus button to save a new one.
          </p>

          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="flex-1">
              <label className="sr-only" htmlFor="studio-saved-job">Use Saved Job</label>
              <select
                id="studio-saved-job"
                value={selectedJobId}
                onChange={(e) => applySelectedJob(e.target.value)}
                className="w-full h-14 px-4 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none bg-white min-w-0 text-base md:text-lg"
              >
                <option value="">{jobsLoading ? "Loading jobs..." : "Select a saved job"}</option>
                {savedJobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title} at {job.company}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-3 justify-center md:justify-start">
              <button
                type="button"
                onClick={(e) => {
                  setSaveModalAnchorRect(e.currentTarget.getBoundingClientRect());
                  setIsSaveModalOpen(true);
                }}
                title="Save new job"
                aria-label="Save new job"
                className="flex-shrink-0 h-14 w-14 rounded-2xl border border-[var(--accent)] bg-[var(--accent)] text-white flex items-center justify-center hover:opacity-90 transition text-[2.3rem] font-light"
              >
                +
              </button>

              <button
                type="button"
                onClick={() => setIsJobDescriptionOpen((prev) => !prev)}
                disabled={!selectedJob}
                title={isJobDescriptionOpen ? "Hide job description" : "View job description"}
                aria-label={isJobDescriptionOpen ? "Hide job description" : "View job description"}
                className="h-14 w-14 rounded-2xl border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isJobDescriptionOpen ? (
                  <svg
                    aria-hidden="true"
                    viewBox="0 0 24 24"
                    className="h-6 w-6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M3 3l18 18" />
                    <path d="M10.6 10.7a2 2 0 0 0 2.7 2.7" />
                    <path d="M9.9 5.1A10.9 10.9 0 0 1 12 4.9c5.1 0 9.3 3 10.8 7.1a11.8 11.8 0 0 1-2.6 3.9" />
                    <path d="M6.2 6.3A12.3 12.3 0 0 0 1.2 12c1.5 4.1 5.7 7.1 10.8 7.1 1.8 0 3.6-.4 5.1-1.1" />
                  </svg>
                ) : (
                  <svg
                    aria-hidden="true"
                    viewBox="0 0 24 24"
                    className="h-6 w-6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M1.2 12C2.7 7.9 6.9 4.9 12 4.9s9.3 3 10.8 7.1C21.3 16.1 17.1 19.1 12 19.1S2.7 16.1 1.2 12Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {selectedJob && (
            <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-sm">
              <span className="inline-flex rounded-full bg-[var(--accent-soft)] text-[var(--accent)] px-3 py-1.5 font-semibold">
                {selectedJob.title}
              </span>
              <span className="inline-flex rounded-full bg-slate-100 text-slate-700 px-3 py-1.5 font-medium">
                {selectedJob.company}
              </span>
            </div>
          )}

          {isJobDescriptionOpen && selectedJob && (
            <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex items-center justify-between gap-4 mb-3">
                <h4 className="font-display font-bold text-slate-900">Job Description</h4>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {selectedJob.title}
                </span>
              </div>
              <div className="max-h-64 overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                {selectedJob.description || "No job description saved for this role yet."}
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="flex flex-col gap-6 min-w-0">
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            {modeOptions.map((mode) => {
              const isActive = activeMode === mode.id;
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => updateMode(mode.id)}
                  className={`rounded-2xl border px-4 py-4 text-left transition ${
                    isActive
                      ? "border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent)]"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <div className="font-display font-bold text-lg">{mode.label}</div>
                  <div className={`mt-1 text-sm ${isActive ? "text-[var(--accent)]" : "text-slate-500"}`}>
                    {mode.description}
                  </div>
                </button>
              );
            })}

            <button
              type="button"
              disabled
              aria-disabled="true"
              title="Workday Skills coming soon"
              className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-4 text-left text-slate-400 cursor-not-allowed"
            >
              <div className="font-display font-bold text-lg">Workday Skills</div>
              <div className="mt-1 text-sm text-slate-400">
                Helps you fill out Workday skills faster.
              </div>
            </button>
          </div>
        </div>

        {activeMode === "resume" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col min-h-[320px]">
              <div>
                <h3 className="font-bold font-display text-lg text-slate-900">Tailored Resume</h3>
                <p className="text-sm text-slate-500 mt-1">
                  Build a targeted resume from the active saved job. Choose PDF for a polished send-ready version or DOCX when you want editable output before applying.
                </p>
              </div>

              <div className="mt-auto pt-8 flex flex-col gap-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => void handleResumeGenerate("pdf")}
                    disabled={loading === "resume"}
                    className="cta-main w-full"
                  >
                    {resumeFormatLoading === "pdf" ? "Generating PDF..." : "Download PDF"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleResumeGenerate("docx")}
                    disabled={loading === "resume"}
                    className="cta-ghost w-full"
                  >
                    {resumeFormatLoading === "docx" ? "Generating DOCX..." : "Download DOCX"}
                  </button>
                </div>

                {resumeStatus && (
                  <div className="rounded-xl border border-[var(--accent-soft)] bg-[var(--accent-soft)]/40 px-4 py-3 text-sm font-medium text-[var(--accent)]">
                    {resumeStatus}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 flex flex-col justify-center items-center text-center min-h-[260px]">
              <div className="w-16 h-16 bg-slate-200 rounded-full mb-4 flex items-center justify-center opacity-50">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              </div>
              <h3 className="font-semibold text-slate-700">Resume Output</h3>
              <p className="text-sm text-slate-500 max-w-sm mt-2">
                Once a saved job is selected, your exports use that description directly. Open the JD above anytime if you want to double-check the active context before downloading.
              </p>
            </div>
          </div>
        )}

        {activeMode === "outreach" && (
          <div className="grid grid-cols-1 lg:grid-cols-[minmax(280px,340px)_1fr] gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col gap-5">
              <div>
                <h3 className="font-bold font-display text-lg text-slate-900">Outreach Generator</h3>
                <p className="text-sm text-slate-500 mt-1">Use the selected saved job as the base context, then choose the format you want to send.</p>
              </div>

              <div className="grid grid-cols-2 gap-2 p-1 rounded-2xl bg-slate-100">
                <button
                  type="button"
                  onClick={() => setOutreachType("cover-letter")}
                  className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
                    outreachType === "cover-letter"
                      ? "bg-white text-[var(--accent)] shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Cover Letter
                </button>
                <button
                  type="button"
                  onClick={() => setOutreachType("cold-email")}
                  className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
                    outreachType === "cold-email"
                      ? "bg-white text-[var(--accent)] shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Cold Email
                </button>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-[var(--accent)]">Company Context (Optional)</label>
                <input
                  type="text"
                  value={companyContext}
                  onChange={(e) => setCompanyContext(e.target.value)}
                  className="h-12 px-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none text-sm"
                  placeholder="e.g. They recently raised Series B"
                />
              </div>

              <button
                type="button"
                onClick={() => void handleOutreachGenerate(outreachType)}
                disabled={outreachLoading !== null}
                className="cta-main w-full"
              >
                {outreachLoading === outreachType
                  ? "Generating..."
                  : outreachType === "cover-letter"
                    ? "Generate Cover Letter"
                    : "Generate Cold Email"}
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col min-h-[340px]">
              <div className="flex items-center justify-between mb-4 gap-4">
                <h3 className="font-bold font-display text-lg text-slate-900">Generated Output</h3>
                {outreachResult && (
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(outreachResult)}
                    className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] hover:underline"
                  >
                    Copy Text
                  </button>
                )}
              </div>

              {outreachResult ? (
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex-1 overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-serif">
                  {outreachResult}
                </div>
              ) : (
                <div className="flex-1 flex flex-col justify-center items-center text-center opacity-60">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><path d="m22 2-7 20-4-9-9-4Z"></path><path d="M22 2 11 13"></path></svg>
                  <p className="text-sm font-medium text-slate-600">Generated outreach will appear here</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeMode === "answers" && (
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex flex-col gap-2 mb-6">
              <label className="text-sm font-semibold text-[var(--accent)]">Application Question</label>
              <textarea
                rows={4}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none resize-y text-sm bg-slate-50"
                placeholder="e.g. Tell us about a time you solved a complex technical problem."
              />
            </div>

            <button
              type="button"
              onClick={handleAnswerGenerate}
              disabled={loading === "answers" || !question.trim()}
              className="cta-main w-full"
            >
              {loading === "answers" ? "Thinking..." : "Generate Answer"}
            </button>

            {answerHistory.length > 0 ? (
              <div className="mt-8 pt-6 border-t border-slate-200 animate-rise" style={{ animationDelay: "50ms" }}>
                <div className="flex justify-between items-center mb-3 gap-4">
                  <h3 className="font-bold text-sm uppercase tracking-wider text-slate-500">Generated Answers</h3>
                  <button
                    type="button"
                    onClick={() => {
                      const compiled = answerHistory
                        .map((entry, index) => `Q${index + 1}: ${entry.question}\nA${index + 1}: ${entry.answer}`)
                        .join("\n\n");
                      void navigator.clipboard.writeText(compiled);
                    }}
                    className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] hover:underline"
                  >
                    Copy All
                  </button>
                </div>
                <div className="flex flex-col gap-3">
                  {answerHistory.map((entry, index) => (
                    <div
                      key={`${entry.question}-${index}`}
                      className="p-4 bg-[var(--background)] rounded-xl border border-[var(--accent-soft)] text-sm leading-relaxed text-slate-800"
                    >
                      <p className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-2">Question</p>
                      <p className="mb-4">{entry.question}</p>
                      <p className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-2">Answer</p>
                      <p>{entry.answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mt-8 pt-8 border-t border-slate-200 flex flex-col items-center justify-center text-center opacity-60 min-h-[220px]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                <p className="text-sm font-medium text-slate-600">Your generated answers will build up here as a reusable response bank.</p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}