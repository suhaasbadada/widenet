import { apiClient } from "./client";

export interface OutreachGenerateResponse {
  subject: string;
  message: string;
}

export interface CoverLetterGenerateResponse {
  cover_letter: string;
}

export interface OutreachCopilotResponse {
  output: string;
}

export async function generateCoverLetter(payload: any): Promise<CoverLetterGenerateResponse> {
  return apiClient<CoverLetterGenerateResponse>("/outreach/cover-letter", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateColdEmail(payload: any): Promise<OutreachGenerateResponse> {
  return apiClient<OutreachGenerateResponse>("/outreach/cold-email", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateCopilot(payload: any): Promise<OutreachCopilotResponse> {
  return apiClient<OutreachCopilotResponse>("/outreach/copilot", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
