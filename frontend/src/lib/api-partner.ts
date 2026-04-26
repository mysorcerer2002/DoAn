import { api } from "@/lib/api";
import type {
  AdminPartnerListRow,
  AdminPartnerMemberRow,
  AdminPartnerStaffRow,
  AdminResetPasswordResponse,
  AdminSettingsResponse,
  AdminUserDetailResponse,
  AdminUserListResponse,
  AdminUserUpdateRequest,
  AuditFeedItem,
  CreateManualTransactionRequest,
  DashboardResponse,
  LedgerEntryResponse,
  LoginLogListResponse,
  MemberResponse,
  PartnerDetailResponse,
  PartnerResponse,
  PartnerSettings,
  PartnerUpdateRequest,
  PlatformStatsResponse,
  PointAdjustmentListResponse,
  PointRuleResponse,
  PointRuleUpdateRequest,
  PointsSummaryResponse,
  RewardCreateRequest,
  RewardResponse,
  RewardUpdateRequest,
  StaffListResponse,
  StaffResetResponse,
  StaffResponse,
  TierResponse,
  TierUpdateRequest,
  TransactionDetailResponse,
  TransactionListResponse,
  TransactionResponse,
  TransactionUpdateRequest,
  TransactionWithMemberResponse,
} from "@/types/partner";

// ==================== Partner Analytics ====================
export const analyticsApi = {
  dashboard: (params?: { from?: string; to?: string }) =>
    api.get<DashboardResponse>("/partner/analytics/dashboard", { params }),
};

// ==================== Partner info / Settings ====================
export const tenantApi = {
  getMe: () => api.get<PartnerResponse>("/partners/me"),
  updateMe: (data: PartnerUpdateRequest) =>
    api.patch<PartnerResponse>("/partners/me", data),
  getSettings: () => api.get<PartnerSettings>("/partners/me/settings"),
  updateSettings: (data: Partial<PartnerSettings>) =>
    api.patch<PartnerSettings>("/partners/me/settings", data),
};

// ==================== Partner Members ====================
export const membersApi = {
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<MemberResponse[]>("/partner/members", { params }),
  get: (id: number) => api.get<MemberResponse>(`/partner/members/${id}`),
  ledger: (id: number, limit = 50) =>
    api.get<LedgerEntryResponse[]>(`/partner/members/${id}/ledger`, {
      params: { limit },
    }),
};

// ==================== Partner Rewards ====================
export const rewardsApi = {
  list: (params?: {
    active_only?: boolean;
    limit?: number;
    offset?: number;
  }) => api.get<RewardResponse[]>("/partner/rewards", { params }),
  get: (id: number) => api.get<RewardResponse>(`/partner/rewards/${id}`),
  create: (data: RewardCreateRequest) =>
    api.post<RewardResponse>("/partner/rewards", data),
  update: (id: number, data: RewardUpdateRequest) =>
    api.patch<RewardResponse>(`/partner/rewards/${id}`, data),
  remove: (id: number) =>
    api.delete<RewardResponse>(`/partner/rewards/${id}`),
};

// ==================== Partner Staff ====================
export const staffApi = {
  list: async (params?: { is_active?: "true" | "false" | "all" }) => {
    const res = await api.get<StaffListResponse>("/partner/staff", { params });
    return res.data;
  },
  add: async (body: {
    email?: string;
    phone?: string;
    full_name: string;
    password: string;
  }) => {
    const res = await api.post<StaffResponse>("/partner/staff", body);
    return res.data;
  },
  toggleActive: async (user_id: number, is_active: boolean) => {
    const res = await api.patch<StaffResponse>(`/partner/staff/${user_id}`, {
      is_active,
    });
    return res.data;
  },
  resetPassword: async (user_id: number) => {
    const res = await api.post<StaffResetResponse>(
      `/partner/staff/${user_id}/reset-password`
    );
    return res.data;
  },
};

// ==================== Partner Transactions ====================
export const transactionsApi = {
  create: (data: CreateManualTransactionRequest) =>
    api.post<TransactionWithMemberResponse>("/partner/transactions", data),
  createFromQr: (data: {
    qr_payload: string;
    gross_amount: number;
    note?: string | null;
  }) =>
    api.post<TransactionWithMemberResponse>(
      "/partner/transactions/qr",
      data
    ),
  list: (params: {
    page?: number;
    page_size?: number;
    date_from?: string;
    date_to?: string;
    q?: string;
  }) =>
    api.get<TransactionListResponse>("/partner/transactions", { params }),
  get: (id: number) =>
    api.get<TransactionDetailResponse>(`/partner/transactions/${id}`),
  update: (id: number, payload: TransactionUpdateRequest) =>
    api.patch<TransactionDetailResponse>(
      `/partner/transactions/${id}`,
      payload
    ),
};

// ==================== Partner Tiers ====================
export const tiersApi = {
  list: () => api.get<TierResponse[]>("/partner/tiers"),
  update: (id: number, data: TierUpdateRequest) =>
    api.patch<TierResponse>(`/partner/tiers/${id}`, data),
};

// ==================== Point Rules ====================
export const pointRulesApi = {
  getActive: () => api.get<PointRuleResponse | null>("/partner/point-rules/active"),
  list: () => api.get<PointRuleResponse[]>("/partner/point-rules"),
  update: (id: number, data: PointRuleUpdateRequest) =>
    api.patch<PointRuleResponse>(`/partner/point-rules/${id}`, data),
};

// ==================== Admin ====================
export const adminApi = {
  stats: () => api.get<PlatformStatsResponse>("/admin/stats"),
  listTenants: (params?: { status?: string }) =>
    api.get<AdminPartnerListRow[]>("/admin/partners", { params }),
  tenantDetail: (id: number) =>
    api.get<PartnerDetailResponse>(`/admin/partners/${id}/detail`),
  tenantStaff: (id: number) =>
    api.get<AdminPartnerStaffRow[]>(`/admin/partners/${id}/staff`),
  tenantMembers: (id: number, params?: { limit?: number; offset?: number }) =>
    api.get<AdminPartnerMemberRow[]>(`/admin/partners/${id}/members`, {
      params,
    }),
  approveTenant: (id: number, approve: boolean, reason?: string) =>
    api.post<PartnerResponse>(`/admin/partners/${id}/approve`, {
      approve,
      reason,
    }),
  suspendTenant: (id: number) =>
    api.post<PartnerResponse>(`/admin/partners/${id}/suspend`),
  listUsers: (params?: {
    q?: string;
    role?: "regular" | "admin" | "super_admin";
    limit?: number;
    offset?: number;
  }) => api.get<AdminUserListResponse>("/admin/users", { params }),
  getUser: (id: number) =>
    api.get<AdminUserDetailResponse>(`/admin/users/${id}`),
  updateUser: (id: number, data: AdminUserUpdateRequest) =>
    api.patch<AdminUserDetailResponse>(`/admin/users/${id}`, data),
  resetUserPassword: (id: number) =>
    api.post<AdminResetPasswordResponse>(`/admin/users/${id}/reset-password`),
  auditFeed: (params?: { limit?: number }) =>
    api.get<AuditFeedItem[]>("/admin/audit-feed", { params }),
  settings: () => api.get<AdminSettingsResponse>("/admin/settings"),
  loginLogs: (params?: {
    identifier?: string;
    success?: boolean;
    from?: string;
    to?: string;
    limit?: number;
    offset?: number;
  }) => api.get<LoginLogListResponse>("/admin/login-logs", { params }),
  pointAdjustments: (params?: {
    user_id?: number;
    partner_id?: number;
    actor_user_id?: number;
    from?: string;
    to?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get<PointAdjustmentListResponse>("/admin/point-adjustments", {
      params,
    }),
  pointsSummary: () =>
    api.get<PointsSummaryResponse>("/admin/points-summary"),
};

// ==================== Customer Extended ====================
export const customerApi = {
  myLedger: (params?: { limit?: number; offset?: number; partner_slug?: string }) =>
    api.get<LedgerEntryResponse[]>("/users/me/ledger", { params }),
};
