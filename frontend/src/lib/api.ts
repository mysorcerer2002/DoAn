import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { getActivePartnerId } from "@/lib/partner-store";
import type {
  LoginRequest,
  Membership,
  RegisterRequest,
  TokenResponse,
  User,
} from "@/types/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Auto-inject X-Partner-Id cho /partner/* và /partners/me/* routes
    const url = config.url ?? "";
    const needsPartner =
      url.startsWith("/partner") || url.startsWith("/partners/me");
    const hasPartnerHeader =
      config.headers && "X-Partner-Id" in config.headers;
    if (needsPartner && !hasPartnerHeader && config.headers) {
      const partnerId = getActivePartnerId();
      if (partnerId != null) {
        config.headers["X-Partner-Id"] = String(partnerId);
      }
    }
  }
  return config;
});

// Single-flight: nhiều request gặp 401 cùng lúc chỉ trigger 1 lần /auth/refresh.
let refreshPromise: Promise<string> | null = null;

async function performRefresh(): Promise<string> {
  if (refreshPromise) return refreshPromise;
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) throw new Error("Missing refresh token");
  refreshPromise = (async () => {
    try {
      // Gọi axios trực tiếp (không qua `api`) để khỏi đệ quy interceptor.
      const resp = await axios.post<TokenResponse>(
        `${API_URL}/auth/refresh`,
        { refresh_token: refreshToken },
        { headers: { "Content-Type": "application/json" } }
      );
      localStorage.setItem("access_token", resp.data.access_token);
      localStorage.setItem("refresh_token", resp.data.refresh_token);
      return resp.data.access_token;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

const NO_REFRESH_PATHS = [
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/auth/forgot-password",
];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (typeof window === "undefined") return Promise.reject(error);
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;
    const url = original?.url ?? "";
    const skip = NO_REFRESH_PATHS.some((p) => url.includes(p));

    if (error.response?.status === 401 && original && !original._retry && !skip) {
      original._retry = true;
      try {
        const newToken = await performRefresh();
        if (original.headers) {
          original.headers.Authorization = `Bearer ${newToken}`;
        }
        return api(original);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data: RegisterRequest) => api.post<TokenResponse>("/auth/register", data),
  login: (data: LoginRequest) => api.post<TokenResponse>("/auth/login", data),
  refresh: (refreshToken: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken }),
  me: () => api.get<User>("/auth/me"),
  updateMe: (data: {
    full_name?: string;
    phone?: string;
    birthday?: string;
  }) => api.patch<User>("/auth/me", data),
};

export const memberApi = {
  listMyMemberships: () => api.get<Membership[]>("/users/me/memberships"),
};
