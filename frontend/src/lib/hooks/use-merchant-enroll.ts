"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  authorizationsApi,
  campaignFeesApi,
  enrollmentApi,
} from "@/lib/api-merchant-enroll";
import { useTenantStore } from "@/lib/tenant-store";
import type { EnrollFormInput } from "@/types/merchant-enroll";

function useTenantId(): number | null {
  return useTenantStore((s) => s.tenant?.id ?? null);
}

// ==================== Templates ====================

export function useEnrollTemplates() {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "enroll-templates", tenantId],
    queryFn: async () => (await enrollmentApi.listTemplates()).data,
    enabled: tenantId != null,
  });
}

// ==================== Preview ====================

export function useEnrollPreview() {
  return useMutation({
    mutationFn: (form: EnrollFormInput) => enrollmentApi.preview(form),
  });
}

// ==================== OTP ====================

export function useRequestEnrollOtp() {
  return useMutation({
    mutationFn: (form: EnrollFormInput) => enrollmentApi.requestOtp(form),
  });
}

// ==================== Sign ====================

export function useSignEnroll() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      form,
      otp_code,
      consent_checked,
    }: {
      form: EnrollFormInput;
      otp_code: string;
      consent_checked: boolean;
    }) => enrollmentApi.sign(form, otp_code, consent_checked),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchant", "campaigns"] });
      qc.invalidateQueries({ queryKey: ["merchant", "authorizations"] });
    },
  });
}

// ==================== Authorizations ====================

export function useAuthorizations() {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "authorizations", tenantId],
    queryFn: async () => (await authorizationsApi.list()).data,
    enabled: tenantId != null,
  });
}

export function useAuthorizationDetail(id: number | null) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "authorizations", "detail", tenantId, id],
    queryFn: async () => (await authorizationsApi.get(id!)).data,
    enabled: tenantId != null && id != null,
  });
}

export function useRevokeAuthorization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      authorizationsApi.revoke(id, reason),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["merchant", "authorizations"] });
      qc.invalidateQueries({
        queryKey: ["merchant", "authorizations", "detail"],
      });
      qc.invalidateQueries({ queryKey: ["merchant", "campaigns"] });
    },
  });
}

// ==================== Service fees ====================

export function useCampaignServiceFees(campaignId: number | null) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "service-fees", tenantId, campaignId],
    queryFn: async () => (await campaignFeesApi.listForCampaign(campaignId!)).data,
    enabled: tenantId != null && campaignId != null,
  });
}
