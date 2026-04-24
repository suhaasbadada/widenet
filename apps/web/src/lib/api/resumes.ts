import { apiClient } from "./client";

export interface ExistingResumeResponse {
  profile_id: string;
  user_id: string;
  structured_profile?: any;
  resume_url?: string;
  updated_at: string;
}

export interface ResumeGenerateResponse {
  resume: any; // the JSON resume output
}

export async function getExistingResume(): Promise<ExistingResumeResponse> {
  return apiClient<ExistingResumeResponse>("/resumes/me", {
    method: "GET",
  });
}

export async function generateTailoredResume(payload: any): Promise<ResumeGenerateResponse> {
  return apiClient<ResumeGenerateResponse>("/resumes/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateAndRenderFile(payload: any): Promise<Blob> {
  return apiClient<Blob>("/resumes/generate-file", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function renderDocx(payload: any): Promise<Blob> {
  return apiClient<Blob>("/resumes/render-docx", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function renderPdf(payload: any): Promise<Blob> {
  return apiClient<Blob>("/resumes/render-pdf", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
