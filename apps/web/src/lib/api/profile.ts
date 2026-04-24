import { apiClient } from "./client";

export interface ProfileLinkItem {
  type: string;
  url: string;
  is_primary?: boolean;
}

export interface ExperienceEntry {
  title?: string;
  company?: string;
  duration?: string; // Legacy
  from?: string;
  to?: string;
  location?: string;
  points?: string[];
}

export interface ProjectEntry {
  name?: string;
  description?: string;
  technologies?: string[];
  from?: string;
  to?: string;
  points?: string[];
}

export interface EducationEntry {
  institution?: string;
  degree?: string;
  major?: string;
  gpa?: string;
  from?: string;
  to?: string;
  location?: string;
}

export interface StructuredProfile {
  experience?: ExperienceEntry[];
  projects?: ProjectEntry[];
  education?: EducationEntry[];
  skills?: Record<string, string[]>;
}

export interface ProfileResponse {
  id: string;
  user_id: string;
  resume_url?: string;
  raw_resume?: string;
  structured_profile?: StructuredProfile;
  name?: string;
  contact_number?: string;
  links?: string[];
  profile_links?: ProfileLinkItem[];
  headline?: string;
  summary?: string;
  created_at: string;
}

export async function uploadResume(file: File): Promise<ProfileResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient<ProfileResponse>("/upload/resume", {
    method: "POST",
    body: formData,
  });
}

export async function getProfile(userId: string): Promise<ProfileResponse> {
  return apiClient<ProfileResponse>(`/profiles/${userId}`, {
    method: "GET",
  });
}

export async function updateProfile(payload: any): Promise<ProfileResponse> {
  return apiClient<ProfileResponse>("/profiles/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function refreshProfile(userId: string): Promise<ProfileResponse> {
  return apiClient<ProfileResponse>(`/profiles/${userId}/refresh`, {
    method: "PUT",
  });
}
