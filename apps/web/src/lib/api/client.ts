export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("widenet_token");
  }
  return null;
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("widenet_token", token);
  }
}

export function clearAuthToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("widenet_token");
  }
}

interface FetchOptions extends RequestInit {
  requiresAuth?: boolean;
}

export async function apiClient<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { requiresAuth = true, headers: customHeaders, ...restOptions } = options;
  
  const headers = new Headers(customHeaders);
  
  // Only set Content-Type to JSON if not explicitly provided and body is not FormData
  if (!headers.has("Content-Type") && !(restOptions.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (requiresAuth) {
    const token = getAuthToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    } else {
      // Could throw or redirect if severely strict, but let FastAPI reject it
    }
  }

  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...restOptions,
    headers,
  });

  if (!response.ok) {
    // Attempt to parse JSON error from FastAPI Exception
    let errorMessage = "An error occurred";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.error || errorMessage;
    } catch {
      // Fallback if not JSON
      errorMessage = await response.text();
    }
    throw new Error(errorMessage);
  }

  // File downloads checks (FastAPI returns FileResponse natively without JSON structure)
  const contentType = response.headers.get("Content-Type");
  const isDocx = contentType === "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  const isPdf = contentType === "application/pdf";
  
  if (isDocx || isPdf) {
     return response.blob() as unknown as Promise<T>; 
  }

  // Default JSON response parsing
  const data = await response.json();
  
  // Widenet API returns { "success": boolean, "data": ... }
  if (data && typeof data === 'object' && "success" in data) {
      if (!data.success) {
          throw new Error(data.error || "API returned success: false");
      }
      return data.data as T;
  }
  
  return data as T;
}
