"use client";

import React, { useEffect, useState } from "react";
import { generateAnswer } from "@/lib/api/answers";
import { listJobs, type JobRecord } from "@/lib/api/jobs";
import { useAuth } from "@/components/providers/AuthProvider";
import SaveNewJobModal from "@/components/jobs/SaveNewJobModal";

type AnswerHistoryItem = {
  question: string;
  answer: string;
};

export default function AnswersPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answerHistory, setAnswerHistory] = useState<AnswerHistoryItem[]>([]);
  const [error, setError] = useState("");
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [saveModalAnchorRect, setSaveModalAnchorRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    const loadJobs = async () => {
      setJobsLoading(true);
      try {
        const savedJobs = await listJobs();
        setJobs(savedJobs);
      } catch (err: any) {
        setError(err.message || "Failed to load saved jobs.");
      } finally {
        setJobsLoading(false);
      }
    };

    void loadJobs();
  }, []);

  const handleGenerate = async () => {
    if (!selectedJobId) {
      setError("Please select a saved job first.");
      return;
    }

    if (!question || question.length < 5) {
      setError("Please ask a valid question.");
      return;
    }
    
    setError("");
    setLoading(true);

    try {
      const resp = await generateAnswer({ 
        user_id: user?.id,
        job_id: selectedJobId,
        question 
      });
      setAnswerHistory((prev) => [
        {
          question: question.trim(),
          answer: resp.answer,
        },
        ...prev,
      ]);
      setQuestion("");
    } catch (err: any) {
      setError(err.message || "Failed to generate answer.");
    } finally {
      setLoading(false);
    }
  };

  const handleNewJobSaved = (job: JobRecord) => {
    setJobs((prev) => [job, ...prev]);
    setSelectedJobId(job.id);
  };

  return (
    <div className="animate-rise">
      <SaveNewJobModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        onSaved={handleNewJobSaved}
        anchorRect={saveModalAnchorRect}
      />
      <div className="mb-8">
        <h2 className="font-display text-3xl font-bold text-slate-900">Application Answers</h2>
        <p className="text-slate-600 mt-2">Generate tailored answers to specific behavioral or functional application questions.</p>
      </div>

      {error && (
        <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-8 font-medium">
          {error}
        </div>
      )}

      <div className="max-w-2xl mx-auto bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex flex-col gap-2 mb-6">
          <label className="text-sm font-semibold text-[var(--accent)]">Select Saved Job</label>
          <div className="flex items-center gap-2">
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="flex-1 h-12 px-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none bg-white min-w-0"
            >
              <option value="">{jobsLoading ? "Loading..." : "Choose one saved job"}</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} at {job.company}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={(e) => {
                setSaveModalAnchorRect(e.currentTarget.getBoundingClientRect());
                setIsSaveModalOpen(true);
              }}
              title="Save new job"
              aria-label="Save new job"
              className="flex-shrink-0 h-12 w-12 rounded-xl border-2 border-[var(--accent)] text-[var(--accent)] flex items-center justify-center hover:bg-[var(--accent-soft)] transition text-2xl font-light"
            >
              +
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-2 mb-6">
          <label className="text-sm font-semibold text-[var(--accent)]">Application Question</label>
          <textarea
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none resize-y text-sm bg-slate-50"
            placeholder="e.g. Tell us about a time you solved a complex technical problem."
          />
        </div>

        <button 
          onClick={handleGenerate} 
          disabled={loading || !question || !selectedJobId} 
          className="cta-main w-full"
        >
          {loading ? "Thinking..." : "Generate Answer"}
        </button>

        {answerHistory.length > 0 && (
          <div className="mt-8 pt-6 border-t border-slate-200 animate-rise" style={{ animationDelay: "50ms" }}>
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-sm uppercase tracking-wider text-slate-500">Generated Answers</h3>
              <button 
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
        )}
      </div>
    </div>
  );
}
