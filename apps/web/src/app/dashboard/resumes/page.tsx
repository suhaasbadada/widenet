"use client";

import React, { useState } from "react";
import { generateAndRenderFile } from "@/lib/api/resumes";

export default function ResumesPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGeneratePdf = async () => {
    if (!jobDescription.trim()) {
      setError("Job Description is required.");
      return;
    }
    
    setError("");
    setLoading(true);

    try {
      const blob = await generateAndRenderFile({
        job_description: jobDescription,
        output_format: "pdf"
      });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "tailored_resume.pdf");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
    } catch (err: any) {
      setError(err.message || "Failed to generate tailored resume PDF.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-rise">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h2 className="font-display text-3xl font-bold text-slate-900">Tailored Resumes</h2>
          <p className="text-slate-600 mt-2">Map your core profile to a specific job description to generate a highly matched resume.</p>
        </div>
      </div>

      {error && (
        <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-8 font-medium">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="font-bold font-display text-lg mb-4">Job Details</h3>
          
          <div className="flex flex-col gap-2 mb-6">
            <label className="text-sm font-semibold text-slate-700">Paste Job Description</label>
            <textarea
              rows={12}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              className="p-3 rounded-xl border border-slate-300 focus:border-[var(--accent)] outline-none resize-y text-sm font-mono leading-relaxed bg-slate-50"
              placeholder="Paste the target job description here..."
            />
          </div>

          <div className="flex gap-4">
            <button 
              onClick={handleGeneratePdf} 
              disabled={loading} 
              className="cta-main flex-1 flex justify-center items-center gap-2"
            >
              {loading ? "Generating..." : "Generate & Download PDF"}
            </button>
          </div>
        </div>

        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 flex flex-col justify-center items-center text-center">
          <div className="w-16 h-16 bg-slate-200 rounded-full mb-4 flex items-center justify-center opacity-50">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          </div>
          <h3 className="font-semibold text-slate-700">Preview Area</h3>
          <p className="text-sm text-slate-500 max-w-sm mt-2">Generate a resume to see structural adaptations before downloading the final file.</p>
        </div>
      </div>
    </div>
  );
}
