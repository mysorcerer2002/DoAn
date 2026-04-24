"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  authorizationsApi,
  campaignFeesApi,
  enrollmentApi,
} from "@/lib/api-partner-enroll";
import { usePartnerStore } from "@/lib/partner-store";
import type { EnrollFormInput } from "@/types/partner-enroll";

function usePartnerId(): number | null {
  return usePartnerStore((s) => s.tenant?.id ?? null);
}

// ==================== Templates ====================

export function useEnrollTemplates() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "enroll-templates", partnerId],
    queryFn: async () => (await enrollmentApi.listTemplates()).data,
    enabled: partnerId != null,
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
      qc.invalidateQueries({ queryKey: ["partner", "campaigns"] });
      qc.invalidateQueries({ queryKey: ["partner", "authorizations"] });
    },
  });
}

// ==================== Authorizations ====================

export function useAuthorizations() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "authorizations", partnerId],
    queryFn: async () => (await authorizationsApi.list()).data,
    enabled: partnerId != null,
  });
}

export function useAuthorizationDetail(id: number | null) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "authorizations", "detail", partnerId, id],
    queryFn: async () => (await authorizationsApi.get(id!)).data,
    enabled: partnerId != null && id != null,
  });
}

export function useRevokeAuthorization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      authorizationsApi.revoke(id, reason),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["partner", "authorizations"] });
      qc.invalidateQueries({
        queryKey: ["partner", "authorizations", "detail"],
      });
      qc.invalidateQueries({ queryKey: ["partner", "campaigns"] });
    },
  });
}

// ==================== Service fees ====================

export function useCampaignServiceFees(campaignId: number | null) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "service-fees", partnerId, campaignId],
    queryFn: async () => (await campaignFeesApi.listForCampaign(campaignId!)).data,
    enabled: partnerId != null && campaignId != null,
  });
}
