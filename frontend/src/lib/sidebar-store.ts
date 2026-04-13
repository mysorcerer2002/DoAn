"use client";

import { create } from "zustand";

interface SidebarState {
  open: boolean;
  toggle: () => void;
  close: () => void;
  setOpen: (open: boolean) => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  open: false,
  toggle: () => set((s) => ({ open: !s.open })),
  close: () => set({ open: false }),
  setOpen: (open) => set({ open }),
}));
