import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/auth";

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
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
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
};
