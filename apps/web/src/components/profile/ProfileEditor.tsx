"use client";

import React, { useState } from "react";
import { ProfileResponse } from "@/lib/api/profile";

interface ProfileEditorProps {
  profileData: Partial<ProfileResponse>;
  setProfileData: (data: Partial<ProfileResponse>) => void;
  onSave: (e: React.FormEvent) => void;
  saving: boolean;
  submitLabel: string;
}

// Normalise em-dash / en-dash variants that LLMs sometimes emit
const normaliseDur = (dur?: string) =>
  (dur || "").replace(/\u2014|\u2013/g, "-");
const getFrom = (dur?: string) => normaliseDur(dur).split("-")[0]?.trim() || "";
const getTo = (dur?: string) => {
  const parts = normaliseDur(dur).split("-");
  return parts.length > 1 ? parts.slice(1).join("-").trim() : "";
};

type TabId = "personal" | "experience" | "education" | "projects";

export function ProfileEditor({ profileData, setProfileData, onSave, saving, submitLabel }: ProfileEditorProps) {
  const [activeTab, setActiveTab] = useState<TabId>("personal");

  const updateField = (field: keyof ProfileResponse, value: any) => {
    setProfileData({ ...profileData, [field]: value });
  };

  const updateStructured = (
    field: "experience" | "projects" | "education",
    value: any
  ) => {
    setProfileData({
      ...profileData,
      structured_profile: {
        ...(profileData.structured_profile || {}),
        [field]: value
      }
    });
  };

  const handleListStringChange = (
    section: "experience" | "projects",
    itemIndex: number,
    field: string,
    bulletIndex: number,
    value: string
  ) => {
    const arr = [...((profileData.structured_profile as any)?.[section] || [])];
    const item = { ...arr[itemIndex] };
    const points = [...(item[field] || [])];
    points[bulletIndex] = value;
    item[field] = points;
    arr[itemIndex] = item;
    updateStructured(section, arr);
  };

  const addPoint = (section: "experience" | "projects", itemIndex: number, field: string = "points") => {
    const arr = [...((profileData.structured_profile as any)?.[section] || [])];
    const item = { ...arr[itemIndex] };
    const points = [...(item[field] || []), ""];
    item[field] = points;
    arr[itemIndex] = item;
    updateStructured(section, arr);
  };

  const removePoint = (section: "experience" | "projects", itemIndex: number, field: string, bulletIndex: number) => {
    const arr = [...((profileData.structured_profile as any)?.[section] || [])];
    const item = { ...arr[itemIndex] };
    const points = [...(item[field] || [])];
    points.splice(bulletIndex, 1);
    item[field] = points;
    arr[itemIndex] = item;
    updateStructured(section, arr);
  };

  const addEntry = (section: "experience" | "projects" | "education") => {
    const arr = [...((profileData.structured_profile as any)?.[section] || [])];
    if (section === "experience") arr.push({ title: "", company: "", duration: "", from: "", to: "", points: [""] });
    if (section === "projects") arr.push({ name: "", description: "", points: [""] });
    if (section === "education") arr.push({ institution: "", degree: "", major: "", from: "", to: "" });
    updateStructured(section, arr);
  };

  const removeEntry = (section: "experience" | "projects" | "education", itemIndex: number) => {
    const arr = [...((profileData.structured_profile as any)?.[section] || [])];
    arr.splice(itemIndex, 1);
    updateStructured(section, arr);
  };

  const inputClass = "w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none text-sm transition-all";
  const labelClass = "text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1 ml-1";

  // SVG Icons
  const TrashIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
  );

  const PlusIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
  );

  const ArrowRight = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
  );

  const tabs: {id: TabId, label: string}[] = [
    { id: "personal", label: "Personal Details" },
    { id: "experience", label: "Experience" },
    { id: "education", label: "Education" },
    { id: "projects", label: "Projects" },
  ];

  return (
    <form onSubmit={onSave} className="flex flex-col md:flex-row gap-6 lg:gap-10 items-start">
      
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 shrink-0 bg-white p-5 rounded-2xl shadow-sm border border-slate-100 md:sticky top-24">
        <nav className="flex flex-col gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center justify-between px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
                activeTab === tab.id 
                  ? "bg-[var(--accent-soft)] text-[var(--accent)] pointer-events-none" 
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              {tab.label}
              {activeTab === tab.id && <ArrowRight />}
            </button>
          ))}
        </nav>
        
        <div className="mt-8 pt-6 border-t border-slate-100">
          <button type="submit" disabled={saving} className="cta-main w-full shadow-md hover:shadow-lg text-[15px] py-4 rounded-xl">
            {saving ? "Saving..." : submitLabel}
          </button>
        </div>
      </aside>

      {/* Main Content Pane */}
      <div className="flex-1 min-w-0 bg-white p-6 md:p-10 lg:p-12 rounded-2xl shadow-sm border border-slate-100">
        
        {/* ----------------- Personal Details ----------------- */}
        {activeTab === "personal" && (
          <div className="animate-rise">
            <h3 className="font-display text-2xl mb-8 text-slate-800">Personal Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col">
                <label className={labelClass}>Full Name</label>
                <input type="text" value={profileData.name || ""} onChange={(e) => updateField("name", e.target.value)} className={inputClass} />
              </div>
              <div className="flex flex-col">
                <label className={labelClass}>Contact Number</label>
                <input type="text" value={profileData.contact_number || ""} onChange={(e) => updateField("contact_number", e.target.value)} className={inputClass} />
              </div>
              <div className="flex flex-col md:col-span-2">
                <label className={labelClass}>Professional Headline</label>
                <input type="text" value={profileData.headline || ""} onChange={(e) => updateField("headline", e.target.value)} className={inputClass} />
              </div>
              <div className="flex flex-col md:col-span-2">
                <label className={labelClass}>Links (Comma separated)</label>
                <input type="text" value={(profileData.links || []).join(", ")} onChange={(e) => updateField("links", e.target.value.split(",").map(s => s.trim()).filter(Boolean))} className={inputClass} placeholder="e.g. linkedin.com/in/user, github.com/user" />
              </div>
              <div className="flex flex-col md:col-span-2">
                <label className={labelClass}>Professional Summary</label>
                <textarea rows={4} value={profileData.summary || ""} onChange={(e) => updateField("summary", e.target.value)} className={`${inputClass} resize-y min-h-[100px] leading-relaxed`} />
              </div>
            </div>
          </div>
        )}

        {/* ----------------- Experience ----------------- */}
        {activeTab === "experience" && (
          <div className="animate-rise">
            <div className="flex justify-between items-end mb-8 border-b border-slate-100 pb-6">
              <h3 className="font-display text-2xl text-slate-800">Experience</h3>
              <button type="button" onClick={() => addEntry("experience")} className="flex items-center gap-2 text-sm font-bold text-[var(--accent)] hover:opacity-70 transition-opacity">
                <PlusIcon /> Add Role
              </button>
            </div>
            {(profileData.structured_profile?.experience || []).length === 0 && (
              <p className="text-slate-500 text-sm italic">No experience entries found.</p>
            )}
            {(profileData.structured_profile?.experience || []).map((exp, index) => (
              <div key={index} className="mb-10 pb-10 border-b border-dashed border-slate-200 last:border-0 last:mb-0 last:pb-0 relative group">
                <button type="button" onClick={() => removeEntry("experience", index)} className="absolute right-0 top-0 p-2 text-slate-300 hover:text-red-500 transition-colors bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-sm border border-slate-100 z-10" title="Delete Role">
                  <TrashIcon />
                </button>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
                  <div className="flex flex-col">
                    <label className={labelClass}>Job Title</label>
                    <input type="text" value={exp.title || ""} onChange={(e) => {
                        const newExp = [...(profileData.structured_profile?.experience || [])];
                        newExp[index].title = e.target.value;
                        updateStructured("experience", newExp);
                      }} className={inputClass} />
                  </div>
                  <div className="flex flex-col">
                    <label className={labelClass}>Company</label>
                    <input type="text" value={exp.company || ""} onChange={(e) => {
                        const newExp = [...(profileData.structured_profile?.experience || [])];
                        newExp[index].company = e.target.value;
                        updateStructured("experience", newExp);
                      }} className={inputClass} />
                  </div>
                  <div className="flex flex-col">
                    <label className={labelClass}>From Date</label>
                    <input type="text" value={exp.from || getFrom(exp.duration)} onChange={(e) => {
                        const newExp = [...(profileData.structured_profile?.experience || [])];
                        newExp[index].from = e.target.value;
                        newExp[index].duration = `${e.target.value} - ${exp.to || getTo(exp.duration)}`;
                        updateStructured("experience", newExp);
                      }} className={inputClass} placeholder="Jan 2021" />
                  </div>
                  <div className="flex flex-col">
                    <label className={labelClass}>To Date</label>
                    <input type="text" value={exp.to || getTo(exp.duration)} onChange={(e) => {
                        const newExp = [...(profileData.structured_profile?.experience || [])];
                        newExp[index].to = e.target.value;
                        newExp[index].duration = `${exp.from || getFrom(exp.duration)} - ${e.target.value}`;
                        updateStructured("experience", newExp);
                      }} className={inputClass} placeholder="Present" />
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <label className={labelClass}>Bullet Points</label>
                  {(exp.points || []).map((pt, pIdx) => (
                    <div key={pIdx} className="flex gap-3 items-start group/bullet">
                      <textarea
                        value={pt}
                        onChange={(e) => handleListStringChange("experience", index, "points", pIdx, e.target.value)}
                        className={`${inputClass} font-serif min-h-[60px] leading-relaxed`}
                      />
                      <button type="button" onClick={() => removePoint("experience", index, "points", pIdx)} className="p-3 text-slate-300 hover:text-red-500 transition-colors mt-1 opacity-0 group-hover/bullet:opacity-100" title="Remove Bullet">
                        <TrashIcon />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addPoint("experience", index)} className="flex items-center gap-1 text-[13px] font-semibold text-slate-500 hover:text-[var(--accent)] self-start mt-1 px-2 py-1 transition-colors">
                    <PlusIcon /> Add Bullet
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ----------------- Education ----------------- */}
        {activeTab === "education" && (
          <div className="animate-rise">
            <div className="flex justify-between items-end mb-8 border-b border-slate-100 pb-6">
              <h3 className="font-display text-2xl text-slate-800">Education</h3>
              <button type="button" onClick={() => addEntry("education")} className="flex items-center gap-2 text-sm font-bold text-[var(--accent)] hover:opacity-70 transition-opacity">
                <PlusIcon /> Add Education
              </button>
            </div>
            {(profileData.structured_profile?.education || []).length === 0 && (
              <p className="text-slate-500 text-sm italic">No education entries found.</p>
            )}
            {(profileData.structured_profile?.education || []).map((edu, index) => (
              <div key={index} className="mb-10 pb-10 border-b border-dashed border-slate-200 last:border-0 last:mb-0 last:pb-0 relative group">
                <button type="button" onClick={() => removeEntry("education", index)} className="absolute right-0 top-0 p-2 text-slate-300 hover:text-red-500 transition-colors bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-sm border border-slate-100 z-10" title="Delete Education">
                  <TrashIcon />
                </button>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="flex flex-col">
                    <label className={labelClass}>Institution</label>
                    <input type="text" value={edu.institution || ""} onChange={(e) => {
                        const newEdu = [...(profileData.structured_profile?.education || [])];
                        newEdu[index].institution = e.target.value;
                        updateStructured("education", newEdu);
                      }} className={inputClass} />
                  </div>
                  <div className="flex flex-col">
                    <label className={labelClass}>Degree & Major</label>
                    <input type="text" value={edu.degree || ""} onChange={(e) => {
                        const newEdu = [...(profileData.structured_profile?.education || [])];
                        newEdu[index].degree = e.target.value;
                        updateStructured("education", newEdu);
                      }} className={inputClass} placeholder="e.g. B.S. Computer Science" />
                  </div>
                  <div className="flex flex-col">
                    <label className={labelClass}>From Date</label>
                    <input type="text" value={edu.from || ""} onChange={(e) => {
                        const newEdu = [...(profileData.structured_profile?.education || [])];
                        newEdu[index].from = e.target.value;
                        updateStructured("education", newEdu);
                      }} className={inputClass} />
                  </div>
                  <div className="flex flex-col">
                    <label className={labelClass}>To Date</label>
                    <input type="text" value={edu.to || ""} onChange={(e) => {
                        const newEdu = [...(profileData.structured_profile?.education || [])];
                        newEdu[index].to = e.target.value;
                        updateStructured("education", newEdu);
                      }} className={inputClass} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* ----------------- Projects ----------------- */}
        {activeTab === "projects" && (
          <div className="animate-rise">
            <div className="flex justify-between items-end mb-8 border-b border-slate-100 pb-6">
              <h3 className="font-display text-2xl text-slate-800">Projects</h3>
              <button type="button" onClick={() => addEntry("projects")} className="flex items-center gap-2 text-sm font-bold text-[var(--accent)] hover:opacity-70 transition-opacity">
                <PlusIcon /> Add Project
              </button>
            </div>
            {(profileData.structured_profile?.projects || []).length === 0 && (
              <p className="text-slate-500 text-sm italic">No projects found.</p>
            )}
            {(profileData.structured_profile?.projects || []).map((proj, index) => (
              <div key={index} className="mb-10 pb-10 border-b border-dashed border-slate-200 last:border-0 last:mb-0 last:pb-0 relative group">
                <button type="button" onClick={() => removeEntry("projects", index)} className="absolute right-0 top-0 p-2 text-slate-300 hover:text-red-500 transition-colors bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-sm border border-slate-100 z-10" title="Delete Project">
                  <TrashIcon />
                </button>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
                  <div className="flex flex-col md:col-span-2">
                    <label className={labelClass}>Project Name</label>
                    <input type="text" value={proj.name || ""} onChange={(e) => {
                        const newProj = [...(profileData.structured_profile?.projects || [])];
                        newProj[index].name = e.target.value;
                        updateStructured("projects", newProj);
                      }} className={inputClass} />
                  </div>
                  <div className="flex flex-col md:col-span-2">
                    <label className={labelClass}>Project Description</label>
                    <input type="text" value={proj.description || ""} onChange={(e) => {
                        const newProj = [...(profileData.structured_profile?.projects || [])];
                        newProj[index].description = e.target.value;
                        updateStructured("projects", newProj);
                      }} className={inputClass} placeholder="Brief one sentence summary" />
                  </div>
                </div>
                <div className="flex flex-col gap-3 mt-2">
                  <label className={labelClass}>Bullet Points</label>
                  {(proj.points || []).map((pt, pIdx) => (
                    <div key={pIdx} className="flex gap-3 items-start group/bullet">
                      <textarea
                        value={pt}
                        onChange={(e) => handleListStringChange("projects", index, "points", pIdx, e.target.value)}
                        className={`${inputClass} font-serif min-h-[60px] leading-relaxed`}
                      />
                      <button type="button" onClick={() => removePoint("projects", index, "points", pIdx)} className="p-3 text-slate-300 hover:text-red-500 transition-colors mt-1 opacity-0 group-hover/bullet:opacity-100" title="Remove Bullet">
                        <TrashIcon />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addPoint("projects", index)} className="flex items-center gap-1 text-[13px] font-semibold text-slate-500 hover:text-[var(--accent)] self-start mt-1 px-2 py-1 transition-colors">
                    <PlusIcon /> Add Bullet
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        
      </div>
    </form>
  );
}
