"use client";

import React, { useState } from "react";
import { generateAnswer } from "@/lib/api/answers";
import { useAuth } from "@/components/providers/AuthProvider";

export default function AnswersPage() {
  const { user } = useAuth();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!question || question.length < 5) {
      setError("Please ask a valid question.");
      return;
    }
    
    setError("");
    setResult("");
    setLoading(true);

    try {
      // Mocking job_id with a neutral UUID until Jobs application tracking is implemented
      const dummyJobId = "00000000-0000-0000-0000-000000000000";
      
      const resp = await generateAnswer({ 
        user_id: user?.id,
        job_id: dummyJobId,
        question 
      });
      setResult(resp.answer);
    } catch (err: any) {
      setError(err.message || "Failed to generate answer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-rise">
      <div className="mb-8">
        <h2 className="font-display text-3xl font-bold text-slate-900">Application Answers</h2>
        <p className="text-slate-600 mt-2">Generate tailored answers to specific behavioral or functional application questions.</p>
      </div>

      {error && (
        <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-8 font-medium">
          {error}
        </div>
      )}

      <div className="max-w-2xl bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex flex-col gap-2 mb-6">
          <label className="text-sm font-semibold text-slate-700">Application Question</label>
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
          disabled={loading || !question} 
          className="cta-main w-full"
        >
          {loading ? "Thinking..." : "Generate Answer"}
        </button>

        {result && (
          <div className="mt-8 pt-6 border-t border-slate-200 animate-rise" style={{ animationDelay: "50ms" }}>
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-sm uppercase tracking-wider text-slate-500">Drafted Answer</h3>
              <button 
                onClick={() => navigator.clipboard.writeText(result)}
                className="text-xs font-bold uppercase tracking-wider text-[var(--accent)] hover:underline"
              >
                Copy Text
              </button>
            </div>
            <div className="p-4 bg-[var(--background)] rounded-xl border border-[var(--accent-soft)] text-sm leading-relaxed text-slate-800">
              {result}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
