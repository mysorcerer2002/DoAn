"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  adminApi,
  analyticsApi,
  customerApi,
  membersApi,
  rewardsApi,
  staffApi,
  tenantApi,
  transactionsApi,
  uploadsApi,
} from "@/lib/api-partner";
import { usePartnerStore } from "@/lib/partner-store";
import type {
  AdminUserUpdateRequest,
  CreateManualTransactionRequest,
  PartnerSettings,
  PartnerUpdateRequest,
  RewardCreateRequest,
  RewardUpdateRequest,
} from "@/types/partner";

function usePartnerId(): number | null {
  return usePartnerStore((s) => s.activePartner?.id ?? null);
}

// ==================== Analytics ====================
export function useDashboard(params?: { from?: string; to?: string }) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "dashboard", partnerId, params?.from, params?.to],
    queryFn: async () => (await analyticsApi.dashboard(params)).data,
    enabled: partnerId != null,
  });
}

// ==================== Partner / Settings ====================
export function useMyPartner() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "me", partnerId],
    queryFn: async () => (await tenantApi.getMe()).data,
    enabled: partnerId != null,
  });
}

export function useMyPartnerSettings() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "settings", partnerId],
    queryFn: async () => (await tenantApi.getSettings()).data,
    enabled: partnerId != null,
  });
}

export function useUpdateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PartnerUpdateRequest) => tenantApi.updateMe(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "me"] }),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<PartnerSettings>) => tenantApi.updateSettings(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "settings"] }),
  });
}

// ==================== Uploads ====================
export function useUploadPartnerImage() {
  return useMutation({
    mutationFn: ({ kind, file }: { kind: "logo" | "banner"; file: File }) =>
      uploadsApi.uploadImage(kind, file),
  });
}

// ==================== Members ====================
export function useMembers(params?: { limit?: number; offset?: number }) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "members", partnerId, params?.limit, params?.offset],
    queryFn: async () => (await membersApi.list(params)).data,
    enabled: partnerId != null,
  });
}

export function useMemberDetail(id: number | null) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "members", partnerId, id],
    queryFn: async () => (await membersApi.get(id!)).data,
    enabled: partnerId != null && id != null,
  });
}

export function useMemberLedger(id: number | null, limit = 50) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "members", partnerId, id, "ledger", limit],
    queryFn: async () => (await membersApi.ledger(id!, limit)).data,
    enabled: partnerId != null && id != null,
  });
}

export function useAdjustMemberPoints() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      delta,
      description,
    }: {
      id: number;
      delta: number;
      description: string;
    }) => membersApi.adjustPoints(id, { delta, description }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "members"] });
      qc.invalidateQueries({ queryKey: ["partner", "dashboard"] });
    },
  });
}

export function useUpdateMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      membersApi.update(id, { is_active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "members"] });
    },
  });
}

// ==================== Rewards ====================
export function useRewards(params?: {
  active_only?: boolean;
  limit?: number;
  offset?: number;
}) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "rewards", partnerId, params],
    queryFn: async () => (await rewardsApi.list(params)).data,
    enabled: partnerId != null,
  });
}

export function useCreateReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: RewardCreateRequest) => rewardsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "rewards"] }),
  });
}

export function useUpdateReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RewardUpdateRequest }) =>
      rewardsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "rewards"] }),
  });
}

export function useDeleteReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => rewardsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "rewards"] }),
  });
}

export function useRewardStats(id: number | null) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "rewards", partnerId, id, "stats"],
    queryFn: async () => (await rewardsApi.stats(id!)).data,
    enabled: partnerId != null && id != null,
  });
}

// ==================== Staff ====================
export function useStaff(filter?: { is_active?: "true" | "false" | "all" }) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "staff", partnerId, filter?.is_active],
    queryFn: () => staffApi.list(filter),
    enabled: partnerId != null,
  });
}

export function useAddStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      email?: string;
      phone?: string;
      full_name: string;
      password: string;
    }) => staffApi.add(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "staff"] }),
  });
}

export function useToggleStaffActive() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      user_id,
      is_active,
    }: {
      user_id: number;
      is_active: boolean;
    }) => staffApi.toggleActive(user_id, is_active),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "staff"] }),
  });
}

export function useResetStaffPassword() {
  return useMutation({
    mutationFn: (user_id: number) => staffApi.resetPassword(user_id),
  });
}

// ==================== Transactions ====================
export function useCreateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateManualTransactionRequest) =>
      transactionsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "transactions"] });
      qc.invalidateQueries({ queryKey: ["partner", "dashboard"] });
      qc.invalidateQueries({ queryKey: ["partner", "members"] });
    },
  });
}

export function useCreateQrTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      qr_payload: string;
      gross_amount: number;
      note?: string | null;
      receipt_code?: string | null;
    }) => transactionsApi.createFromQr(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "transactions"] });
      qc.invalidateQueries({ queryKey: ["partner", "dashboard"] });
      qc.invalidateQueries({ queryKey: ["partner", "members"] });
    },
  });
}

export function useLookupCustomerByPhone(phone: string, enabled: boolean) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "lookup", "phone", partnerId, phone],
    queryFn: async () => (await transactionsApi.lookupByPhone(phone)).data,
    enabled: enabled && partnerId != null,
    retry: false,
    staleTime: 30_000,
  });
}

export function useLookupCustomerByQr(qr: string, enabled: boolean) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "lookup", "qr", partnerId, qr],
    queryFn: async () => (await transactionsApi.lookupByQr(qr)).data,
    enabled: enabled && partnerId != null,
    retry: false,
    staleTime: 30_000,
  });
}

// ==================== Admin ====================
export function usePlatformStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: async () => (await adminApi.stats()).data,
  });
}

export function useAdminTenants(status?: string) {
  return useQuery({
    queryKey: ["admin", "partners", status],
    queryFn: async () => (await adminApi.listTenants({ status })).data,
  });
}

export function useAdminTenantDetail(partnerId: number | null) {
  return useQuery({
    queryKey: ["admin", "partners", "detail", partnerId],
    queryFn: async () => (await adminApi.tenantDetail(partnerId as number)).data,
    enabled: partnerId != null,
  });
}

export function useAdminTenantStaff(partnerId: number | null) {
  return useQuery({
    queryKey: ["admin", "partners", "staff", partnerId],
    queryFn: async () => (await adminApi.tenantStaff(partnerId as number)).data,
    enabled: partnerId != null,
  });
}

export function useAdminTenantMembers(
  partnerId: number | null,
  params?: { limit?: number; offset?: number },
) {
  return useQuery({
    queryKey: ["admin", "partners", "members", partnerId, params],
    queryFn: async () =>
      (await adminApi.tenantMembers(partnerId as number, params)).data,
    enabled: partnerId != null,
  });
}

export function useApproveTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      approve,
      reason,
    }: {
      id: number;
      approve: boolean;
      reason?: string;
    }) => adminApi.approveTenant(id, approve, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "partners"] });
      qc.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
}

// ==================== Customer extras ====================
export function useMyLedger(params?: { limit?: number; offset?: number; partnerSlug?: string }) {
  const { partnerSlug, ...rest } = params ?? {};
  const apiParams = { ...rest, ...(partnerSlug ? { partner_slug: partnerSlug } : {}) };
  return useQuery({
    queryKey: ["customer", "ledger", apiParams],
    queryFn: async () => (await customerApi.myLedger(apiParams)).data,
  });
}

// ==================== Admin extensions ====================
export function useAdminUsers(params?: {
  q?: string;
  role?: "regular" | "admin" | "super_admin";
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["admin", "users", params],
    queryFn: async () => (await adminApi.listUsers(params)).data,
  });
}

export function useAdminUserDetail(userId: number | null) {
  return useQuery({
    queryKey: ["admin", "users", "detail", userId],
    queryFn: async () => (await adminApi.getUser(userId as number)).data,
    enabled: userId != null,
  });
}

export function useUpdateAdminUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AdminUserUpdateRequest }) =>
      adminApi.updateUser(id, data),
    onSuccess: (_res, vars) => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      qc.invalidateQueries({
        queryKey: ["admin", "users", "detail", vars.id],
      });
    },
  });
}

export function useResetAdminUserPassword() {
  return useMutation({
    mutationFn: (id: number) => adminApi.resetUserPassword(id),
  });
}

export function useAdminAuditFeed(limit = 30) {
  return useQuery({
    queryKey: ["admin", "audit-feed", limit],
    queryFn: async () => (await adminApi.auditFeed({ limit })).data,
  });
}

export function useAdminSettings() {
  return useQuery({
    queryKey: ["admin", "settings"],
    queryFn: async () => (await adminApi.settings()).data,
  });
}

