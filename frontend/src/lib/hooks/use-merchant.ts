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
} from "@/lib/api-merchant";
import { useTenantStore } from "@/lib/tenant-store";
import type {
  AdminUserUpdateRequest,
  CampaignCreateRequest,
  CreateManualTransactionRequest,
  RewardCreateRequest,
  RewardUpdateRequest,
  StaffAddRequest,
  TenantSettings,
  TenantUpdateRequest,
} from "@/types/merchant";

function useTenantId(): number | null {
  return useTenantStore((s) => s.tenant?.id ?? null);
}

// ==================== Analytics ====================
export function useDashboard(params?: { from?: string; to?: string }) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "dashboard", tenantId, params?.from, params?.to],
    queryFn: async () => (await analyticsApi.dashboard(params)).data,
    enabled: tenantId != null,
  });
}

// ==================== Tenant / Settings ====================
export function useMyTenant() {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "tenant", tenantId],
    queryFn: async () => (await tenantApi.getMe()).data,
    enabled: tenantId != null,
  });
}

export function useMyTenantSettings() {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "settings", tenantId],
    queryFn: async () => (await tenantApi.getSettings()).data,
    enabled: tenantId != null,
  });
}

export function useUpdateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TenantUpdateRequest) => tenantApi.updateMe(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "tenant"] }),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<TenantSettings>) => tenantApi.updateSettings(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "settings"] }),
  });
}

// ==================== Members ====================
export function useMembers(params?: { limit?: number; offset?: number }) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "members", tenantId, params?.limit, params?.offset],
    queryFn: async () => (await membersApi.list(params)).data,
    enabled: tenantId != null,
  });
}

export function useMemberDetail(id: number | null) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "members", tenantId, id],
    queryFn: async () => (await membersApi.get(id!)).data,
    enabled: tenantId != null && id != null,
  });
}

// ==================== Rewards ====================
export function useRewards(params?: {
  active_only?: boolean;
  limit?: number;
  offset?: number;
}) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "rewards", tenantId, params],
    queryFn: async () => (await rewardsApi.list(params)).data,
    enabled: tenantId != null,
  });
}

export function useCreateReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: RewardCreateRequest) => rewardsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "rewards"] }),
  });
}

export function useUpdateReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RewardUpdateRequest }) =>
      rewardsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "rewards"] }),
  });
}

export function useDeleteReward() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => rewardsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "rewards"] }),
  });
}

// ==================== Campaigns ====================
export function useCampaigns(params?: { active_only?: boolean }) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "campaigns", tenantId, params],
    queryFn: async () => (await campaignsApi.list(params)).data,
    enabled: tenantId != null,
  });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignCreateRequest) => campaignsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "campaigns"] }),
  });
}

export function useCampaignDetail(id: number | null) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "campaigns", "detail", tenantId, id],
    queryFn: async () => (await campaignsApi.get(id as number)).data,
    enabled: tenantId != null && id != null,
  });
}

export function useCampaignRoi(id: number | null) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "campaigns", "roi", tenantId, id],
    queryFn: async () => (await campaignsApi.roi(id as number)).data,
    enabled: tenantId != null && id != null,
  });
}

// ==================== Staff ====================
export function useStaff() {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "staff", tenantId],
    queryFn: async () => (await staffApi.list()).data,
    enabled: tenantId != null,
  });
}

export function useAddStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: StaffAddRequest) => staffApi.add(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "staff"] }),
  });
}

export function useRemoveStaff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => staffApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["merchant", "staff"] }),
  });
}

// ==================== Transactions ====================
export function useTransactions(params?: { limit?: number; offset?: number }) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "transactions", tenantId, params],
    queryFn: async () => (await transactionsApi.list(params)).data,
    enabled: tenantId != null,
  });
}

export function useCreateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateManualTransactionRequest) =>
      transactionsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchant", "transactions"] });
      qc.invalidateQueries({ queryKey: ["merchant", "dashboard"] });
      qc.invalidateQueries({ queryKey: ["merchant", "members"] });
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
      qc.invalidateQueries({ queryKey: ["merchant", "transactions"] });
      qc.invalidateQueries({ queryKey: ["merchant", "dashboard"] });
      qc.invalidateQueries({ queryKey: ["merchant", "members"] });
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
    queryKey: ["admin", "tenants", status],
    queryFn: async () => (await adminApi.listTenants({ status })).data,
  });
}

export function useAdminTenantDetail(tenantId: number | null) {
  return useQuery({
    queryKey: ["admin", "tenants", "detail", tenantId],
    queryFn: async () => (await adminApi.tenantDetail(tenantId as number)).data,
    enabled: tenantId != null,
  });
}

export function useAdminTenantStaff(tenantId: number | null) {
  return useQuery({
    queryKey: ["admin", "tenants", "staff", tenantId],
    queryFn: async () => (await adminApi.tenantStaff(tenantId as number)).data,
    enabled: tenantId != null,
  });
}

export function useAdminTenantMembers(
  tenantId: number | null,
  params?: { limit?: number; offset?: number },
) {
  return useQuery({
    queryKey: ["admin", "tenants", "members", tenantId, params],
    queryFn: async () =>
      (await adminApi.tenantMembers(tenantId as number, params)).data,
    enabled: tenantId != null,
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
      qc.invalidateQueries({ queryKey: ["admin", "tenants"] });
      qc.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
}

// ==================== Customer extras ====================
export function useMyLedger(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["customer", "ledger", params],
    queryFn: async () => (await customerApi.myLedger(params)).data,
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

// ==================== Merchant Vouchers ====================
export function useMerchantVouchers(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}) {
  const tenantId = useTenantId();
  return useQuery({
    queryKey: ["merchant", "vouchers", tenantId, params],
    queryFn: async () => (await merchantVouchersApi.list(params)).data,
    enabled: tenantId != null,
  });
}
