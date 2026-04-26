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

const formatToMonth = (dateStr?: string) => {
  if (!dateStr || dateStr.toLowerCase() === "present") return "";
  
  // Handle MM/YYYY format
  const mmYyyyMatch = dateStr.match(/^(\d{1,2})\/(\d{4})$/);
  if (mmYyyyMatch) {
    return `${mmYyyyMatch[2]}-${mmYyyyMatch[1].padStart(2, '0')}`;
  }

  // Try parsing Jan 2021 etc.
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) {
    const parts = dateStr.split(/\s+/);
    if (parts.length === 2) {
      const monthNames = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
      const mIdx = monthNames.findIndex(m => parts[0].toLowerCase().startsWith(m));
      if (mIdx !== -1 && /^\d{4}$/.test(parts[1])) {
        return `${parts[1]}-${String(mIdx + 1).padStart(2, '0')}`;
      }
    }
    return "";
  }
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

const formatFromMonth = (monthStr: string) => {
  if (!monthStr) return "";
  const [year, month] = monthStr.split("-");
  return `${month}/${year}`;
};

const MonthPicker = ({ value, onChange, placeholder }: { value: string, onChange: (val: string) => void, placeholder?: string }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  
  const parts = (value || "").split("/");
  const selectedMonth = parts[0] ? parseInt(parts[0]) - 1 : -1;
  const selectedYear = parts[1] ? parseInt(parts[1]) : -1;

  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  return (
    <div className="relative">
      <div className="relative group/picker">
        <input 
          type="text" 
          value={value} 
          readOnly 
          onClick={() => {
            setIsOpen(!isOpen);
            if (!isOpen && selectedYear !== -1) setCurrentYear(selectedYear);
          }}
          className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none text-sm transition-all bg-white min-h-[48px] cursor-pointer pr-10"
          placeholder={placeholder || "MM/YYYY"}
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-hover/picker:text-[var(--accent)] transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      </div>
      
      {isOpen && (
        <>
          <div className="fixed inset-0 z-[60]" onClick={() => setIsOpen(false)} />
          <div 
            className="absolute top-full left-0 md:left-auto md:right-0 mt-2 w-64 bg-white rounded-2xl shadow-2xl border border-slate-100 p-4 z-[70] animate-in fade-in zoom-in-95 duration-200 origin-top"
            style={{ display: 'block', minWidth: '240px' }}
          >
            <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-50">
              <button type="button" onClick={() => setCurrentYear(currentYear - 1)} className="p-1.5 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-[var(--accent)] transition-all">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </button>
              <span className="font-bold text-slate-800 text-base">{currentYear}</span>
              <button type="button" onClick={() => setCurrentYear(currentYear + 1)} className="p-1.5 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-[var(--accent)] transition-all">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </button>
            </div>
            <div 
              style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(3, 1fr)', 
                gap: '8px' 
              }}
            >
              {months.map((m, i) => {
                const isSelected = selectedMonth === i && selectedYear === currentYear;
                return (
                  <button
                    key={m}
                    type="button"
                    onClick={() => {
                      const mStr = (i + 1).toString().padStart(2, '0');
                      onChange(`${mStr}/${currentYear}`);
                      setIsOpen(false);
                    }}
                    className={`py-2 text-[12px] font-bold rounded-lg transition-all border ${
                      isSelected 
                        ? "bg-[var(--accent)] text-white border-[var(--accent)] shadow-md shadow-[var(--accent)]/20 scale-105" 
                        : "text-slate-600 bg-white border-transparent hover:border-slate-100 hover:bg-slate-50 hover:text-[var(--accent)]"
                    }`}
                  >
                    {m}
                  </button>
                );
              })}
            </div>
            <div className="mt-3 pt-2 border-t border-slate-50 flex justify-center">
               <button 
                type="button"
                onClick={() => {
                  const now = new Date();
                  const mStr = (now.getMonth() + 1).toString().padStart(2, '0');
                  onChange(`${mStr}/${now.getFullYear()}`);
                  setIsOpen(false);
                }}
                className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent)] hover:bg-slate-50 px-2 py-1 rounded-lg transition-all"
               >
                Current Month
               </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

type TabId = "personal" | "experience" | "education" | "projects";

export function ProfileEditor({ profileData, setProfileData, onSave, saving, submitLabel }: ProfileEditorProps) {
  const [activeTab, setActiveTab] = useState<TabId>("personal");
  const [expandedExperienceIndex, setExpandedExperienceIndex] = useState<number | null>(null);
  const [expandedEducationIndex, setExpandedEducationIndex] = useState<number | null>(null);
  const [expandedProjectIndex, setExpandedProjectIndex] = useState<number | null>(null);

  const updateField = (field: keyof ProfileResponse, value: any) => {
    setProfileData({ ...profileData, [field]: value });
  };

  const getLinks = (): string[] => {
    const links = profileData.links;
    if (!Array.isArray(links)) {
      return [];
    }
    return links.map((link) => String(link ?? ""));
  };

  const setLinks = (links: string[]) => {
    const normalized = links.map((link) => link.trim()).filter(Boolean);
    updateField("links", normalized);
  };

  const updateLinkAt = (index: number, value: string) => {
    const links = getLinks();
    links[index] = value;
    updateField("links", links);
  };

  const normalizeLinkAt = (index: number) => {
    const links = getLinks();
    const raw = links[index] || "";

    // If users paste comma-separated links into one field, split it automatically.
    if (raw.includes(",")) {
      const expanded = raw
        .split(",")
        .map((part) => part.trim())
        .filter(Boolean);
      links.splice(index, 1, ...expanded);
      setLinks(links);
      return;
    }

    links[index] = raw.trim();
    setLinks(links);
  };

  const addLink = () => {
    const links = getLinks();
    updateField("links", [...links, ""]);
  };

  const removeLinkAt = (index: number) => {
    const links = getLinks();
    links.splice(index, 1);
    setLinks(links);
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
    if (section === "experience") {
      arr.push({ title: "", company: "", location: "", duration: "", from: "", to: "", points: [""] });
      setExpandedExperienceIndex(arr.length - 1);
    }
    if (section === "projects") {
      arr.push({ name: "", description: "", technologies: [""], points: [""] });
      setExpandedProjectIndex(arr.length - 1);
    }
    if (section === "education") {
      arr.push({ institution: "", degree: "", major: "", location: "", from: "", to: "", gpa: "" });
      setExpandedEducationIndex(arr.length - 1);
    }
    updateStructured(section, arr);
  };

  const removeEntry = (section: "experience" | "projects" | "education", itemIndex: number) => {
    const arr = [...((profileData.structured_profile as any)?.[section] || [])];
    arr.splice(itemIndex, 1);
    updateStructured(section, arr);

    if (section === "experience") {
      setExpandedExperienceIndex((prev) => {
        if (prev === null) {
          return prev;
        }
        if (prev === itemIndex) {
          return null;
        }
        return prev > itemIndex ? prev - 1 : prev;
      });
    }

    if (section === "projects") {
      setExpandedProjectIndex((prev) => {
        if (prev === null) {
          return prev;
        }
        if (prev === itemIndex) {
          return null;
        }
        return prev > itemIndex ? prev - 1 : prev;
      });
    }

    if (section === "education") {
      setExpandedEducationIndex((prev) => {
        if (prev === null) {
          return prev;
        }
        if (prev === itemIndex) {
          return null;
        }
        return prev > itemIndex ? prev - 1 : prev;
      });
    }
  };

  const inputClass = "w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] outline-none text-sm transition-all bg-white min-h-[48px]";
  const labelClass = "text-[11px] font-bold uppercase tracking-wider text-[var(--accent)] mb-1 ml-1";

  // SVG Icons
  const TrashIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
  );

  const PlusIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14" /><path d="M12 5v14" /></svg>
  );

  const ArrowRight = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
  );

  const ChevronDown = ({ open }: { open: boolean }) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`transition-transform ${open ? "rotate-180" : "rotate-0"}`}
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );

  const tabs: { id: TabId, label: string }[] = [
    { id: "personal", label: "Personal Details" },
    { id: "experience", label: "Experience" },
    { id: "education", label: "Education" },
    { id: "projects", label: "Projects" },
  ];

  return (
    <form onSubmit={onSave} className="flex flex-col md:flex-row gap-6 lg:gap-10 items-start pb-20">

      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 shrink-0 bg-white p-5 rounded-2xl shadow-sm border border-slate-100 md:sticky top-24">
        <nav className="flex flex-col gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center justify-between px-4 py-3 text-sm font-semibold rounded-xl transition-all ${activeTab === tab.id
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
                <label className={labelClass}>Links</label>
                <div className="flex flex-col gap-3">
                  {getLinks().length === 0 ? (
                    <div className="text-sm text-slate-500">No links added yet.</div>
                  ) : (
                    getLinks().map((link, index) => (
                      <div key={`${index}-${link}`} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={link}
                          onChange={(e) => updateLinkAt(index, e.target.value)}
                          onBlur={() => normalizeLinkAt(index)}
                          className={inputClass}
                          placeholder="e.g. https://linkedin.com/in/user"
                        />
                        <button
                          type="button"
                          onClick={() => removeLinkAt(index)}
                          className="p-2 text-slate-400 hover:text-red-500 transition-colors rounded-lg"
                          title="Remove Link"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    ))
                  )}

                  <button
                    type="button"
                    onClick={addLink}
                    className="flex items-center gap-1 text-[13px] font-semibold text-slate-500 hover:text-[var(--accent)] self-start mt-1 px-2 py-1 transition-colors"
                  >
                    <PlusIcon /> Add Link
                  </button>
                </div>
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
              <div key={index} className="mb-5 rounded-xl border border-slate-200 bg-white">
                <div className="flex items-center justify-between gap-3 px-4 py-3">
                  <button
                    type="button"
                    onClick={() => setExpandedExperienceIndex((prev) => (prev === index ? null : index))}
                    className="flex min-w-0 flex-1 items-center justify-between gap-3 text-left"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-800">{exp.title || "Untitled Role"}</p>
                      <p className="truncate text-sm text-slate-500">{exp.company || "Company not set"}</p>
                    </div>
                    <span className="text-slate-500">
                      <ChevronDown open={expandedExperienceIndex === index} />
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => removeEntry("experience", index)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors rounded-lg"
                    title="Delete Role"
                  >
                    <TrashIcon />
                  </button>
                </div>

                {expandedExperienceIndex === index && (
                  <div className="border-t border-slate-100 px-4 pb-4 pt-4">
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
                        <label className={labelClass}>Location</label>
                        <input type="text" value={exp.location || ""} onChange={(e) => {
                          const newExp = [...(profileData.structured_profile?.experience || [])];
                          newExp[index].location = e.target.value;
                          updateStructured("experience", newExp);
                        }} className={inputClass} placeholder="e.g. New York, NY" />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col">
                          <label className={labelClass}>From</label>
                          <MonthPicker
                            value={exp.from || ""}
                            onChange={(val) => {
                              const newExp = [...(profileData.structured_profile?.experience || [])];
                              newExp[index].from = val;
                              newExp[index].duration = `${val} - ${exp.to || getTo(exp.duration)}`;
                              updateStructured("experience", newExp);
                            }}
                          />
                        </div>
                        <div className="flex flex-col">
                          <div className="flex justify-between items-center mb-1">
                            <label className={labelClass.replace("mb-1", "")}>To</label>
                            <button
                              type="button"
                              onClick={() => {
                                const newExp = [...(profileData.structured_profile?.experience || [])];
                                newExp[index].to = "Present";
                                newExp[index].duration = `${exp.from || getFrom(exp.duration)} - Present`;
                                updateStructured("experience", newExp);
                              }}
                              className="text-[10px] font-bold text-[var(--accent)] hover:underline"
                            >
                              Present
                            </button>
                          </div>
                          {exp.to?.toLowerCase() === "present" ? (
                            <div className="relative">
                              <input
                                type="text"
                                value="Present"
                                readOnly
                                className={`${inputClass} cursor-default`}
                              />
                              <button
                                type="button"
                                onClick={() => {
                                  const newExp = [...(profileData.structured_profile?.experience || [])];
                                  newExp[index].to = "01/" + new Date().getFullYear();
                                  updateStructured("experience", newExp);
                                }}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-slate-100 px-2 py-1 rounded text-slate-600 hover:bg-slate-200"
                              >
                                Change
                              </button>
                            </div>
                          ) : (
                            <MonthPicker
                              value={exp.to || ""}
                              onChange={(val) => {
                                const newExp = [...(profileData.structured_profile?.experience || [])];
                                newExp[index].to = val;
                                newExp[index].duration = `${exp.from || getFrom(exp.duration)} - ${val}`;
                                updateStructured("experience", newExp);
                              }}
                            />
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col gap-3">
                      <label className={labelClass}>Key Achievements</label>
                      {(exp.points || []).map((pt, pIdx) => (
                        <div key={pIdx} className="relative group/bullet">
                          <textarea
                            value={pt}
                            onChange={(e) => handleListStringChange("experience", index, "points", pIdx, e.target.value)}
                            className={`${inputClass} min-h-[60px] leading-relaxed pr-10`}
                          />
                          <button type="button" onClick={() => removePoint("experience", index, "points", pIdx)} className="absolute top-2 right-2 p-1.5 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover/bullet:opacity-100 bg-white rounded-lg shadow-sm border border-slate-100" title="Remove Achievement">
                            <TrashIcon />
                          </button>
                        </div>
                      ))}
                      <button type="button" onClick={() => addPoint("experience", index)} className="flex items-center gap-1 text-[13px] font-semibold text-slate-500 hover:text-[var(--accent)] self-start mt-1 px-2 py-1 transition-colors">
                        <PlusIcon /> Add Achievement
                      </button>
                    </div>
                  </div>
                )}
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
              <div key={index} className="mb-5 rounded-xl border border-slate-200 bg-white">
                <div className="flex items-center justify-between gap-3 px-4 py-3">
                  <button
                    type="button"
                    onClick={() => setExpandedEducationIndex((prev) => (prev === index ? null : index))}
                    className="flex min-w-0 flex-1 items-center justify-between gap-3 text-left"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-800">{edu.institution || "Institution not set"}</p>
                      <p className="truncate text-sm text-slate-500">{edu.degree || "Degree not set"}</p>
                    </div>
                    <span className="text-slate-500">
                      <ChevronDown open={expandedEducationIndex === index} />
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => removeEntry("education", index)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors rounded-lg"
                    title="Delete Education"
                  >
                    <TrashIcon />
                  </button>
                </div>

                {expandedEducationIndex === index && (
                  <div className="border-t border-slate-100 px-4 pb-4 pt-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                      <div className="flex flex-col col-span-2">
                        <label className={labelClass}>Institution</label>
                        <input type="text" value={edu.institution || ""} onChange={(e) => {
                          const newEdu = [...(profileData.structured_profile?.education || [])];
                          newEdu[index].institution = e.target.value;
                          updateStructured("education", newEdu);
                        }} className={inputClass} />
                      </div>
                      <div className="flex flex-col col-span-2">
                        <label className={labelClass}>Degree</label>
                        <input type="text" value={edu.degree || ""} onChange={(e) => {
                          const newEdu = [...(profileData.structured_profile?.education || [])];
                          newEdu[index].degree = e.target.value;
                          updateStructured("education", newEdu);
                        }} className={inputClass} placeholder="e.g. Bachelor of Science" />
                      </div>
                      <div className="flex flex-col col-span-2">
                        <label className={labelClass}>Major</label>
                        <input type="text" value={edu.major || ""} onChange={(e) => {
                          const newEdu = [...(profileData.structured_profile?.education || [])];
                          newEdu[index].major = e.target.value;
                          updateStructured("education", newEdu);
                        }} className={inputClass} placeholder="e.g. Computer Science" />
                      </div>
                      <div className="flex flex-col col-span-2">
                        <label className={labelClass}>Location</label>
                        <input type="text" value={edu.location || ""} onChange={(e) => {
                          const newEdu = [...(profileData.structured_profile?.education || [])];
                          newEdu[index].location = e.target.value;
                          updateStructured("education", newEdu);
                        }} className={inputClass} placeholder="e.g. San Francisco, CA" />
                      </div>

                      <div className="flex flex-col col-span-1">
                        <label className={labelClass}>From</label>
                        <MonthPicker
                          value={edu.from || ""}
                          onChange={(val) => {
                            const newEdu = [...(profileData.structured_profile?.education || [])];
                            newEdu[index].from = val;
                            updateStructured("education", newEdu);
                          }}
                        />
                      </div>
                      <div className="flex flex-col col-span-1">
                        <div className="flex justify-between items-center mb-1">
                          <label className={labelClass.replace("mb-1", "")}>To</label>
                          <button
                            type="button"
                            onClick={() => {
                              const newEdu = [...(profileData.structured_profile?.education || [])];
                              newEdu[index].to = "Present";
                              updateStructured("education", newEdu);
                            }}
                            className="text-[10px] font-bold text-[var(--accent)] hover:underline"
                          >
                            Present
                          </button>
                        </div>
                        {edu.to?.toLowerCase() === "present" ? (
                          <div className="relative">
                            <input
                              type="text"
                              value="Present"
                              readOnly
                              className={`${inputClass} cursor-default`}
                            />
                            <button
                              type="button"
                              onClick={() => {
                                const newEdu = [...(profileData.structured_profile?.education || [])];
                                newEdu[index].to = "01/" + new Date().getFullYear();
                                updateStructured("education", newEdu);
                              }}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-slate-100 px-2 py-1 rounded text-slate-600 hover:bg-slate-200"
                            >
                              Change
                            </button>
                          </div>
                        ) : (
                          <MonthPicker
                            value={edu.to || ""}
                            onChange={(val) => {
                              const newEdu = [...(profileData.structured_profile?.education || [])];
                              newEdu[index].to = val;
                              updateStructured("education", newEdu);
                            }}
                          />
                        )}
                      </div>
                      <div className="flex flex-col col-span-2">
                        <label className={labelClass}>GPA (optional)</label>
                        <input type="text" value={edu.gpa || ""} onChange={(e) => {
                          const newEdu = [...(profileData.structured_profile?.education || [])];
                          newEdu[index].gpa = e.target.value;
                          updateStructured("education", newEdu);
                        }} className={inputClass} placeholder="e.g. 3.8 / 4.0" />
                      </div>
                    </div>
                  </div>
                )}
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
              <div key={index} className="mb-5 rounded-xl border border-slate-200 bg-white">
                <div className="flex items-center justify-between gap-3 px-4 py-3">
                  <button
                    type="button"
                    onClick={() => setExpandedProjectIndex((prev) => (prev === index ? null : index))}
                    className="flex min-w-0 flex-1 items-center justify-between gap-3 text-left"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-800">{proj.name || "Untitled Project"}</p>
                      <p className="truncate text-sm text-slate-500">{proj.description || "Description not set"}</p>
                    </div>
                    <span className="text-slate-500">
                      <ChevronDown open={expandedProjectIndex === index} />
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => removeEntry("projects", index)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors rounded-lg"
                    title="Delete Project"
                  >
                    <TrashIcon />
                  </button>
                </div>

                {expandedProjectIndex === index && (
                  <div className="border-t border-slate-100 px-4 pb-4 pt-4">
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

                    <div className="flex flex-col gap-3 mb-5">
                      <label className={labelClass}>Tech Skills (Comma Separated)</label>
                      <input
                        type="text"
                        value={(proj.technologies || []).join(", ")}
                        onChange={(e) => {
                          const newProj = [...(profileData.structured_profile?.projects || [])];
                          newProj[index].technologies = e.target.value
                            .split(",")
                            .map((item) => item.trim())
                            .filter(Boolean);
                          updateStructured("projects", newProj);
                        }}
                        className={inputClass}
                        placeholder="e.g. React, FastAPI, PostgreSQL"
                      />
                    </div>

                    <div className="flex flex-col gap-3 mt-2">
                      <label className={labelClass}>Key Achievements</label>
                      {(proj.points || []).map((pt, pIdx) => (
                        <div key={pIdx} className="relative group/bullet">
                          <textarea
                            value={pt}
                            onChange={(e) => handleListStringChange("projects", index, "points", pIdx, e.target.value)}
                            className={`${inputClass} min-h-[60px] leading-relaxed pr-10`}
                          />
                          <button type="button" onClick={() => removePoint("projects", index, "points", pIdx)} className="absolute top-2 right-2 p-1.5 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover/bullet:opacity-100 bg-white rounded-lg shadow-sm border border-slate-100" title="Remove Achievement">
                            <TrashIcon />
                          </button>
                        </div>
                      ))}
                      <button type="button" onClick={() => addPoint("projects", index)} className="flex items-center gap-1 text-[13px] font-semibold text-slate-500 hover:text-[var(--accent)] self-start mt-1 px-2 py-1 transition-colors">
                        <PlusIcon /> Add Achievement
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

      </div>
    </form>
  );
}
