"use client";

import React, { useEffect, useState } from "react";
import { getProfile, updateProfile, ProfileResponse } from "@/lib/api/profile";
import { useAuth } from "@/components/providers/AuthProvider";
import { ProfileEditor } from "@/components/profile/ProfileEditor";

export default function ProfilePage() {
  const { user } = useAuth();
  const [profileData, setProfileData] = useState<Partial<ProfileResponse>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });

  useEffect(() => {
    if (user?.id) {
      getProfile(user.id)
        .then(data => {
          setProfileData(data);
        })
        .catch(err => {
          setMessage({ text: "Failed to load profile. You may need to complete onboarding.", type: "error" });
        })
        .finally(() => setLoading(false));
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ text: "", type: "" });

    try {
      await updateProfile(profileData);
      setMessage({ text: "Profile updated successfully.", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to save profile updates.", type: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse flex space-x-4"><div className="flex-1 space-y-4 py-1"><div className="h-4 bg-slate-200 rounded w-3/4"></div></div></div>;
  }

  return (
    <div className="animate-rise">
      <div className="mb-8">
        <h2 className="font-display text-3xl font-bold text-slate-900">Your Core Profile</h2>
        <p className="text-slate-600 mt-2">This data acts as the source of truth for all tailored generations.</p>
      </div>

      {message.text && (
        <div className={`p-4 rounded-xl mb-8 font-medium ${message.type === 'error' ? 'bg-[var(--warning-soft)] text-[var(--warning)]' : 'bg-[var(--accent-soft)] text-[var(--accent)]'}`}>
          {message.text}
        </div>
      )}

      <ProfileEditor 
        profileData={profileData} 
        setProfileData={setProfileData} 
        onSave={handleSave} 
        saving={saving} 
        submitLabel="Save Changes" 
      />
    </div>
  );
}
