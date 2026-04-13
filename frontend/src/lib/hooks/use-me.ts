"use client";

import { useQuery } from "@tanstack/react-query";
import { authApi, memberApi } from "@/lib/api";
import type { Membership, User } from "@/types/auth";

function hasToken(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(sessionStorage.getItem("access_token"));
}

export function useMe() {
  return useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const res = await authApi.me();
      return res.data;
    },
    enabled: hasToken(),
  });
}

export function useMyMemberships() {
  return useQuery<Membership[]>({
    queryKey: ["member", "memberships"],
    queryFn: async () => {
      const res = await memberApi.listMyMemberships();
      return res.data;
    },
    enabled: hasToken(),
  });
}
