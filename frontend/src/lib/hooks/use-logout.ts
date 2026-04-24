"use client";

import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { useAuthStore } from "@/lib/auth-store";
import { usePartnerStore } from "@/lib/partner-store";

/** Logout: clear token + partner + cache + redirect /login. */
export function useLogout() {
  const router = useRouter();
  const qc = useQueryClient();
  const logoutStore = useAuthStore((s) => s.logout);
  const setActivePartner = usePartnerStore((s) => s.setActivePartner);

  return () => {
    logoutStore();
    setActivePartner(null);
    qc.clear();
    router.replace("/login");
  };
}
