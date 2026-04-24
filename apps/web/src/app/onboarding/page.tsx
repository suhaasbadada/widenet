"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { uploadResume, updateProfile, ProfileResponse } from "@/lib/api/profile";
import { useAuth } from "@/components/providers/AuthProvider";
import { ProfileEditor } from "@/components/profile/ProfileEditor";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  
  const [step, setStep] = useState<1 | 2>(1);
  const [file, setFile] = useState<File | null>(null);
  
  // Profile state for editing
  const [profileData, setProfileData] = useState<Partial<ProfileResponse>>({});
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    
    setError("");
    setLoading(true);

    try {
      const resp = await uploadResume(file);
      setProfileData(resp);
      setStep(2);
    } catch (err: any) {
      setError(err.message || "Failed to upload and parse resume.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await updateProfile({
        name: profileData.name,
        contact_number: profileData.contact_number,
        headline: profileData.headline,
        summary: profileData.summary,
        // We aren't fully formatting links Array/Dict here to keep MVP simple
      });
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to save profile updates.");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <main className="page-shell flex items-center justify-center">Loading or unauthorized...</main>;
  }

  return (
    <main className="page-shell min-h-screen py-16 px-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-display text-4xl font-bold text-slate-900 mb-2">Welcome to Widenet</h1>
        <p className="text-lg text-slate-600 mb-10">Let's set up your profile so we can generate tailored content.</p>

        {error && (
          <div className="bg-[var(--warning-soft)] text-[var(--warning)] p-4 rounded-xl mb-8 font-medium">
            {error}
          </div>
        )}

        {step === 1 && (
          <form onSubmit={handleUpload} className="bg-[var(--panel)] p-8 rounded-2xl shadow-sm border border-slate-200 animate-rise">
            <h2 className="text-xl font-bold mb-4 font-display">Step 1: Upload your resume</h2>
            <p className="text-sm text-slate-600 mb-6">We accept PDF and DOCX files. Our AI will automatically extract your experience, skills, and summary.</p>
            
            <div className="flex flex-col gap-4">
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[var(--accent-soft)] file:text-[var(--accent)] hover:file:bg-[#c1e6e0] cursor-pointer"
              />
              <button 
                type="submit" 
                disabled={!file || loading}
                className="cta-main self-start mt-4 disabled:opacity-50"
              >
                {loading ? "Parsing Resume..." : "Upload & Parse"}
              </button>
            </div>
          </form>
        )}

        {step === 2 && (
          <div className="animate-rise">
            <h2 className="text-xl font-bold mb-4 font-display">Step 2: Review your extracted profile</h2>
            <p className="text-sm text-slate-600 mb-8">Make any adjustments before we save this as your core operating profile.</p>

            <ProfileEditor 
              profileData={profileData} 
              setProfileData={setProfileData} 
              onSave={handleSaveProfile} 
              saving={loading} 
              submitLabel="Save & Continue to Dashboard" 
            />
          </div>
        )}
      </div>
    </main>
  );
}
