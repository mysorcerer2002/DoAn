"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { pointRulesApi, tiersApi } from "@/lib/api-partner";
import { usePartnerStore } from "@/lib/partner-store";
import type { PointRuleUpdateRequest, TierUpdateRequest } from "@/types/partner";

function usePartnerId(): number | null {
  return usePartnerStore((s) => s.activePartner?.id ?? null);
}

// ==================== Point Rules ====================

export function useActivePointRule() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "point-rule", "active", partnerId],
    queryFn: async () => (await pointRulesApi.getActive()).data,
    enabled: partnerId != null,
  });
}

export function useUpdatePointRule(ruleId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PointRuleUpdateRequest) =>
      pointRulesApi.update(ruleId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "point-rule"] });
    },
  });
}

// ==================== Tiers ====================

export function usePartnerTiers() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "tiers", partnerId],
    queryFn: async () => (await tiersApi.list()).data,
    enabled: partnerId != null,
  });
}

export function useUpdateTier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TierUpdateRequest }) =>
      tiersApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "tiers"] });
    },
  });
}
