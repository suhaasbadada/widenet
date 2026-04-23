type HealthResponse = {
  status: string;
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
    const data = await fetchJson<HealthResponse>("/health");
    return { ok: data.status === "ok", status: data.status };
  } catch {
    return { ok: false, status: "down" };
  }
}
