import { api } from "@/lib/api";
import type {
  AdminSettingsResponse,
  AdminUserListResponse,
  AuditFeedItem,
  CampaignCreateRequest,
  CampaignResponse,
  CreateManualTransactionRequest,
  DashboardResponse,
  LedgerEntryResponse,
  MemberResponse,
  PlatformStatsResponse,
  RewardCreateRequest,
  RewardResponse,
  RewardUpdateRequest,
  StaffAddRequest,
  StaffAddResponse,
  StaffResponse,
  TenantDetailResponse,
  TenantResponse,
  TenantSettings,
  TenantUpdateRequest,
  TierResponse,
  TransactionResponse,
  TransactionWithMemberResponse,
  VoucherResponse,
} from "@/types/merchant";

// ==================== Merchant Analytics ====================
export const analyticsApi = {
  dashboard: (params?: { from?: string; to?: string }) =>
    api.get<DashboardResponse>("/merchant/analytics/dashboard", { params }),
};

// ==================== Merchant Tenant ====================
export const tenantApi = {
  getMe: () => api.get<TenantResponse>("/tenants/me"),
  updateMe: (data: TenantUpdateRequest) =>
    api.patch<TenantResponse>("/tenants/me", data),
  getSettings: () => api.get<TenantSettings>("/tenants/me/settings"),
  updateSettings: (data: Partial<TenantSettings>) =>
    api.patch<TenantSettings>("/tenants/me/settings", data),
};

// ==================== Merchant Members ====================
export const membersApi = {
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<MemberResponse[]>("/merchant/members", { params }),
  get: (id: number) => api.get<MemberResponse>(`/merchant/members/${id}`),
  ledger: (id: number, limit = 50) =>
    api.get<LedgerEntryResponse[]>(`/merchant/members/${id}/ledger`, {
      params: { limit },
    }),
};

// ==================== Merchant Rewards ====================
export const rewardsApi = {
  list: (params?: {
    active_only?: boolean;
    limit?: number;
    offset?: number;
  }) => api.get<RewardResponse[]>("/merchant/rewards", { params }),
  get: (id: number) => api.get<RewardResponse>(`/merchant/rewards/${id}`),
  create: (data: RewardCreateRequest) =>
    api.post<RewardResponse>("/merchant/rewards", data),
  update: (id: number, data: RewardUpdateRequest) =>
    api.patch<RewardResponse>(`/merchant/rewards/${id}`, data),
  remove: (id: number) =>
    api.delete<RewardResponse>(`/merchant/rewards/${id}`),
};

// ==================== Merchant Campaigns ====================
export const campaignsApi = {
  list: (params?: { active_only?: boolean }) =>
    api.get<CampaignResponse[]>("/merchant/campaigns", { params }),
  get: (id: number) => api.get<CampaignResponse>(`/merchant/campaigns/${id}`),
  create: (data: CampaignCreateRequest) =>
    api.post<CampaignResponse>("/merchant/campaigns", data),
  update: (id: number, data: Partial<CampaignCreateRequest>) =>
    api.patch<CampaignResponse>(`/merchant/campaigns/${id}`, data),
  remove: (id: number) => api.delete(`/merchant/campaigns/${id}`),
};

// ==================== Merchant Staff ====================
export const staffApi = {
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<StaffResponse[]>("/merchant/staff", { params }),
  add: (data: StaffAddRequest) =>
    api.post<StaffAddResponse>("/merchant/staff", data),
  updateRole: (id: number, role: "owner" | "staff") =>
    api.patch<StaffResponse>(`/merchant/staff/${id}`, { role }),
  remove: (id: number) => api.delete(`/merchant/staff/${id}`),
};

// ==================== Merchant Transactions ====================
export const transactionsApi = {
  create: (data: CreateManualTransactionRequest) =>
    api.post<TransactionWithMemberResponse>("/merchant/transactions", data),
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<TransactionResponse[]>("/merchant/transactions", { params }),
};

// ==================== Merchant Tiers ====================
export const tiersApi = {
  list: () => api.get<TierResponse[]>("/merchant/tiers"),
};

// ==================== Admin ====================
export const adminApi = {
  stats: () => api.get<PlatformStatsResponse>("/admin/stats"),
  listTenants: (params?: { status?: string }) =>
    api.get<TenantResponse[]>("/admin/tenants", { params }),
  tenantDetail: (id: number) =>
    api.get<TenantDetailResponse>(`/admin/tenants/${id}/detail`),
  approveTenant: (id: number, approve: boolean, reason?: string) =>
    api.post<TenantResponse>(`/admin/tenants/${id}/approve`, {
      approve,
      reason,
    }),
  suspendTenant: (id: number) =>
    api.post<TenantResponse>(`/admin/tenants/${id}/suspend`),
  listUsers: (params?: {
    q?: string;
    role?: "regular" | "admin" | "super_admin";
    limit?: number;
    offset?: number;
  }) => api.get<AdminUserListResponse>("/admin/users", { params }),
  auditFeed: (params?: { limit?: number }) =>
    api.get<AuditFeedItem[]>("/admin/audit-feed", { params }),
  settings: () => api.get<AdminSettingsResponse>("/admin/settings"),
};

// ==================== Merchant Vouchers ====================
export const merchantVouchersApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    api.get<VoucherResponse[]>("/merchant/vouchers", { params }),
};

// ==================== Customer Extended ====================
export const customerApi = {
  myLedger: (params?: { limit?: number; offset?: number }) =>
    api.get<LedgerEntryResponse[]>("/users/me/ledger", { params }),
  myVouchers: (params?: { status?: string }) =>
    api.get<VoucherResponse[]>("/users/me/vouchers", { params }),
};
