import { apiClient } from "./client";

export interface JobRecord {
  id: string;
  title: string;
  company: string;
  description: string | null;
  created_at: string;
}

export interface CreateJobPayload {
  title: string;
  company: string;
  description?: string;
}

export async function listJobs(): Promise<JobRecord[]> {
  return apiClient<JobRecord[]>("/jobs", {
    method: "GET",
  });
}

export async function createJob(payload: CreateJobPayload): Promise<JobRecord> {
  return apiClient<JobRecord>("/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
