"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  adminApi,
  analyticsApi,
  campaignsApi,
  customerApi,
  membersApi,
  merchantVouchersApi,
  rewardsApi,
  staffApi,
  tenantApi,
  transactionsApi,
} from "@/lib/api-partner";
import { usePartnerStore } from "@/lib/partner-store";
import type {
  AdminUserUpdateRequest,
  CampaignCreateRequest,
  CreateManualTransactionRequest,
  PartnerSettings,
  PartnerUpdateRequest,
  RewardCreateRequest,
  RewardUpdateRequest,
  StaffAddRequest,
} from "@/types/partner";

function usePartnerId(): number | null {
  return usePartnerStore((s) => s.tenant?.id ?? null);
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

// ==================== Tenant / Settings ====================
export function useMyTenant() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "tenant", partnerId],
    queryFn: async () => (await tenantApi.getMe()).data,
    enabled: partnerId != null,
  });
}

export function useMyTenantSettings() {
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "tenant"] }),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<PartnerSettings>) => tenantApi.updateSettings(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "settings"] }),
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

// ==================== Campaigns ====================
export function useCampaigns(params?: { active_only?: boolean }) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "campaigns", partnerId, params],
    queryFn: async () => (await campaignsApi.list(params)).data,
    enabled: partnerId != null,
  });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignCreateRequest) => campaignsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "campaigns"] }),
  });
}

export function useCampaignDetail(id: number | null) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "campaigns", "detail", partnerId, id],
    queryFn: async () => (await campaignsApi.get(id as number)).data,
    enabled: partnerId != null && id != null,
  });
}

export function useCampaignRoi(id: number | null) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "campaigns", "roi", partnerId, id],
    queryFn: async () => (await campaignsApi.roi(id as number)).data,
    enabled: partnerId != null && id != null,
  });
}

// ==================== Staff ====================
export function useStaff() {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "staff", partnerId],
    queryFn: async () => (await staffApi.list()).data,
    enabled: partnerId != null,
  });
}

export function useAddStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: StaffAddRequest) => staffApi.add(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "staff"] }),
  });
}

export function useRemoveStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => staffApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["partner", "staff"] }),
  });
}

// ==================== Transactions ====================
export function useTransactions(params?: { limit?: number; offset?: number }) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "transactions", partnerId, params],
    queryFn: async () => (await transactionsApi.list(params)).data,
    enabled: partnerId != null,
  });
}

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
    }) => transactionsApi.createFromQr(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner", "transactions"] });
      qc.invalidateQueries({ queryKey: ["partner", "dashboard"] });
      qc.invalidateQueries({ queryKey: ["partner", "members"] });
    },
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

export function useMyVouchers(params?: { status?: string }) {
  return useQuery({
    queryKey: ["customer", "vouchers", params?.status],
    queryFn: async () => (await customerApi.myVouchers(params)).data,
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

// ==================== Partner Vouchers ====================
export function useMerchantVouchers(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}) {
  const partnerId = usePartnerId();
  return useQuery({
    queryKey: ["partner", "vouchers", partnerId, params],
    queryFn: async () => (await merchantVouchersApi.list(params)).data,
    enabled: partnerId != null,
  });
}
