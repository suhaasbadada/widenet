import { apiClient } from "./client";

export interface AnswerGenerateResponse {
  answer: string;
}

export async function generateAnswer(payload: any): Promise<AnswerGenerateResponse> {
  return apiClient<AnswerGenerateResponse>("/answers/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
