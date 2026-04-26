"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api-partner";

export function useSystemPoints() {
  return useQuery({
    queryKey: ["system-points"],
    queryFn: async () => (await adminApi.pointsSummary()).data,
  });
}
