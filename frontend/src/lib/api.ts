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
    const token = sessionStorage.getItem("access_token");
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

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      window.location.href = "/login";
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
