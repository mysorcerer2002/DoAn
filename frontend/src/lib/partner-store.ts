"use client";

import { create } from "zustand";

const STORAGE_KEY = "active_partner";

type StoredPartner = {
  id: number;
  name: string;
  slug: string;
  role: string;
};

interface PartnerState {
  activePartner: StoredPartner | null;
  setActivePartner: (partner: StoredPartner | null) => void;
  rehydrate: () => void;
}

function readStored(): StoredPartner | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredPartner;
  } catch {
    return null;
  }
}

export const usePartnerStore = create<PartnerState>((set) => ({
  activePartner: null,

  setActivePartner: (partner) => {
    if (typeof window !== "undefined") {
      if (partner) {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(partner));
      } else {
        sessionStorage.removeItem(STORAGE_KEY);
      }
    }
    set({ activePartner: partner });
  },

  rehydrate: () => {
    const stored = readStored();
    if (stored) set({ activePartner: stored });
  },
}));

/** Đọc partner id hiện tại từ sessionStorage (sync) — dùng trong axios interceptor. */
export function getActivePartnerId(): number | null {
  const stored = readStored();
  return stored?.id ?? null;
}
