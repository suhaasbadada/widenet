import { apiClient, setAuthToken, clearAuthToken } from "./client";

export interface UserResponse {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const data = await apiClient<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
    requiresAuth: false,
  });
  setAuthToken(data.access_token);
  return data;
}

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const data = await apiClient<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    requiresAuth: false,
  });
  setAuthToken(data.access_token);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await apiClient<{ logged_out: boolean }>("/auth/logout", {
      method: "POST",
    });
  } catch (err) {
    console.error("Logout API failed, continuing client-side logout:", err);
  } finally {
    clearAuthToken();
  }
}

export async function changePassword(payload: ChangePasswordPayload): Promise<void> {
  await apiClient<{ password_changed: boolean }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
