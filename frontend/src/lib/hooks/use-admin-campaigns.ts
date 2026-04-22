"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminCampaignsApi, campaignTemplatesApi } from "@/lib/api-admin";
import type {
  CampaignTemplateCreateRequest,
  CampaignTemplateUpdateRequest,
  RejectCampaignRequest,
  RegulatorySubmissionRequest,
} from "@/types/admin";

// ==================== Campaign Templates ====================

export function useCampaignTemplates(filters?: {
  source?: string;
  is_active?: boolean;
  include_deleted?: boolean;
}) {
  return useQuery({
    queryKey: ["admin", "templates", filters],
    queryFn: async () => (await campaignTemplatesApi.list(filters)).data,
  });
}

export function useCampaignTemplate(id: number | null) {
  return useQuery({
    queryKey: ["admin", "templates", id],
    queryFn: async () => (await campaignTemplatesApi.get(id as number)).data,
    enabled: id != null,
  });
}

export function useCreateCampaignTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignTemplateCreateRequest) =>
      campaignTemplatesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "templates"] }),
  });
}

export function useUpdateCampaignTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CampaignTemplateUpdateRequest }) =>
      campaignTemplatesApi.update(id, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["admin", "templates"] });
      qc.invalidateQueries({ queryKey: ["admin", "templates", vars.id] });
    },
  });
}

export function useSoftDeleteCampaignTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => campaignTemplatesApi.softDelete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "templates"] }),
  });
}

// ==================== Admin Approval Queue ====================

export function usePendingCampaigns(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["admin", "campaigns", "pending", params],
    queryFn: async () => (await adminCampaignsApi.listPending(params)).data,
  });
}

export function useOverdueReports() {
  return useQuery({
    queryKey: ["admin", "campaigns", "overdue"],
    queryFn: async () => (await adminCampaignsApi.listOverdue()).data,
  });
}

export function useAdminCampaignDetail(id: number | null) {
  return useQuery({
    queryKey: ["admin", "campaigns", "detail", id],
    queryFn: async () => (await adminCampaignsApi.getDetail(id as number)).data,
    enabled: id != null,
  });
}

export function useCampaignEvents(id: number | null) {
  return useQuery({
    queryKey: ["admin", "campaigns", "events", id],
    queryFn: async () => (await adminCampaignsApi.listEvents(id as number)).data,
    enabled: id != null,
  });
}

export function useMarkOpsStarted() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => adminCampaignsApi.markOpsStarted(id),
    onSuccess: (_res, id) => {
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "detail", id] });
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "events", id] });
    },
  });
}

export function useAddRegulatorySubmission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RegulatorySubmissionRequest }) =>
      adminCampaignsApi.addRegulatorySubmission(id, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "detail", vars.id] });
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "events", vars.id] });
    },
  });
}

export function useApproveCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => adminCampaignsApi.approve(id),
    onSuccess: (_res, id) => {
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "detail", id] });
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "pending"] });
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "events", id] });
    },
  });
}

export function useRejectCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RejectCampaignRequest }) =>
      adminCampaignsApi.reject(id, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "detail", vars.id] });
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "pending"] });
      qc.invalidateQueries({ queryKey: ["admin", "campaigns", "events", vars.id] });
    },
  });
}
