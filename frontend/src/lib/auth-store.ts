import { create } from "zustand";
import type { User } from "@/types/auth";
import { authApi } from "./api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  fetchMe: () => Promise<void>;
  logout: () => void;
  rehydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,

  setTokens: (accessToken, refreshToken) => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("access_token", accessToken);
      sessionStorage.setItem("refresh_token", refreshToken);
    }
  },

  fetchMe: async () => {
    set({ isLoading: true });
    try {
      const { data } = await authApi.me();
      set({ user: data, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },

  logout: () => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
    }
    set({ user: null });
  },

  rehydrate: async () => {
    if (typeof window === "undefined") return;
    const token = sessionStorage.getItem("access_token");
    if (!token) return;
    set({ isLoading: true });
    try {
      const { data } = await authApi.me();
      set({ user: data, isLoading: false });
    } catch {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      set({ user: null, isLoading: false });
    }
  },
}));
