"use client";

import { create } from "zustand";

const STORAGE_KEY = "active_tenant";

type StoredTenant = {
  id: number;
  name: string;
  slug: string;
  role: string;
};

interface TenantState {
  tenant: StoredTenant | null;
  setTenant: (tenant: StoredTenant | null) => void;
  rehydrate: () => void;
}

function readStored(): StoredTenant | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredTenant;
  } catch {
    return null;
  }
}

export const useTenantStore = create<TenantState>((set) => ({
  tenant: null,

  setTenant: (tenant) => {
    if (typeof window !== "undefined") {
      if (tenant) {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(tenant));
      } else {
        sessionStorage.removeItem(STORAGE_KEY);
      }
    }
    set({ tenant });
  },

  rehydrate: () => {
    const stored = readStored();
    if (stored) set({ tenant: stored });
  },
}));

/** Đọc tenant id hiện tại từ sessionStorage (sync) — dùng trong axios interceptor. */
export function getActiveTenantId(): number | null {
  const stored = readStored();
  return stored?.id ?? null;
}
