import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api-partner";

interface UseAdminAuditLogsParams {
  actor_user_id?: number;
  target_type?: "user" | "partner";
  target_id?: number;
  action?: string;
  limit?: number;
  offset?: number;
}

export function useAdminAuditLogs(params: UseAdminAuditLogsParams = {}) {
  return useQuery({
    queryKey: ["admin", "audit-logs", params],
    queryFn: async () => {
      const res = await adminApi.auditLogs(params);
      return res.data;
    },
  });
}
