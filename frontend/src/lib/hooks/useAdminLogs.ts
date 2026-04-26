"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api-partner";

export function useAdminLoginLogs(filters: {
  identifier?: string;
  success?: boolean;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["admin-login-logs", filters],
    queryFn: async () => (await adminApi.loginLogs(filters)).data,
  });
}

export function useAdminPointAdjustments(filters: {
  user_id?: number;
  partner_id?: number;
  actor_user_id?: number;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["admin-point-adjustments", filters],
    queryFn: async () => (await adminApi.pointAdjustments(filters)).data,
  });
}
