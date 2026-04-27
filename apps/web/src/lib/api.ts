type HealthResponse = {
  status: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  data: T;
};

export type ProfileLinkItem = {
  type: string;
  url: string;
  is_primary?: boolean;
};

export type ProfileResponse = {
  id: string;
  user_id: string;
  resume_url: string | null;
  raw_resume: string | null;
  structured_profile: Record<string, unknown> | null;
  name: string | null;
  contact_number: string | null;
  links: string[] | null;
  profile_links: ProfileLinkItem[] | null;
  headline: string | null;
  summary: string | null;
  created_at: string;
};

export type UpdateProfileRequest = {
  resume_url?: string | null;
  raw_resume?: string | null;
  structured_profile?: Record<string, unknown> | null;
  name?: string | null;
  contact_number?: string | null;
  links?: Array<string | ProfileLinkItem> | null;
  headline?: string | null;
  summary?: string | null;
};

type ResumeProfileOverrides = {
  name?: string;
  contact_number?: string;
  links?: string[];
  summary?: string;
  skills?: Record<string, string[]> | Array<Record<string, unknown>>;
  experience?: Array<Record<string, unknown>>;
  projects?: Array<Record<string, unknown>>;
  education?: Array<Record<string, unknown>>;
};

export type GenerateResumeFileRequest = {
  job_description: string;
  output_format: "docx" | "pdf";
  file_name?: string;
  profile_overrides?: ResumeProfileOverrides;
  template_path?: string;
  docx_file_name?: string;
  pdf_file_name?: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getApiHealth(): Promise<{ ok: boolean; status: string }> {
  try {
    // Always check /health at the API base URL root
    const data = await fetchJson<HealthResponse>("/health");
    return { ok: data.status === "ok", status: data.status };
  } catch {
    // Try /api/v1/health as fallback (for legacy or misconfigured deployments)
    try {
      const data = await fetchJson<HealthResponse>("/api/v1/health");
      return { ok: data.status === "ok", status: data.status };
    } catch {
      return { ok: false, status: "down" };
    }
  }
}

export async function getProfileByUserId(
  userId: string,
): Promise<ProfileResponse> {
  const response = await fetchJson<ApiEnvelope<ProfileResponse>>(
    `/api/v1/profiles/${userId}`,
  );
  return response.data;
}

export async function updateMyProfile(
  token: string,
  payload: UpdateProfileRequest,
): Promise<ProfileResponse> {
  const response = await fetchJson<ApiEnvelope<ProfileResponse>>(
    "/api/v1/profiles/me",
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  );
  return response.data;
}

export async function refreshProfile(
  token: string,
  userId: string,
): Promise<ProfileResponse> {
  const response = await fetchJson<ApiEnvelope<ProfileResponse>>(
    `/api/v1/profiles/${userId}/refresh`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  return response.data;
}

export async function generateResumeFileOneClick(
  token: string,
  payload: GenerateResumeFileRequest,
): Promise<{ blob: Blob; fileName: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/generate-file`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^\"]+)"?/i);
  const fallbackName = payload.output_format === "docx" ? "resume.docx" : "resume.pdf";
  const fileName = match?.[1] || payload.file_name || fallbackName;

  return { blob, fileName };
}

export function triggerBrowserDownload(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
