// Types cho partner / admin / shared API responses

export interface PartnerStaffSummary {
  id: number;
  name: string;
  slug: string;
  logo_url: string | null;
  status: string;
  role: string;
}

export interface PartnerResponse {
  id: number;
  name: string;
  slug: string;
  owner_user_id: number;
  status: string;
  category: string;
  logo_url: string | null;
  banner_url: string | null;
  description: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  address: string | null;
  tax_code: string | null;
  website: string | null;
  business_hours: string | null;
  settings: Record<string, unknown>;
  created_at: string;
  activated_at: string | null;
}

export interface PartnerUpdateRequest {
  name?: string;
  description?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  category?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  address?: string | null;
  tax_code?: string | null;
  website?: string | null;
  business_hours?: string | null;
}

// Members
export interface MemberResponse {
  membership_id: number;
  tenant_id: number;
  user_id: number;
  user_phone: string | null;
  user_full_name: string | null;
  user_email: string | null;
  points_balance: number;
  total_points_earned: number;
  current_tier_id: number | null;
  current_tier_name: string | null;
  joined_at: string;
  last_activity_at: string | null;
  is_new: boolean;
}

// Rewards
export interface RewardResponse {
  id: number;
  tenant_id: number;
  name: string;
  description: string | null;
  points_cost: number;
  stock: number | null;
  is_active: boolean;
  image_url: string | null;
  created_at: string;
  deleted_at: string | null;
}

export interface RewardCreateRequest {
  name: string;
  description?: string | null;
  points_cost: number;
  stock?: number | null;
  is_active?: boolean;
  image_url?: string | null;
}

export interface RewardUpdateRequest {
  name?: string;
  description?: string | null;
  points_cost?: number;
  stock?: number | null;
  is_active?: boolean;
  image_url?: string | null;
}

// Staff
export interface StaffResponse {
  id: number;
  user_id: number;
  email: string | null;
  phone: string | null;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface StaffListResponse {
  items: StaffResponse[];
  total: number;
}

export interface StaffAddRequest {
  email?: string;
  phone?: string;
  full_name: string;
  password: string;
}

export interface StaffResetResponse {
  email_sent: boolean;
  temp_password: string;
  message: string;
}

// Transactions
export interface TransactionResponse {
  id: number;
  tenant_id: number;
  membership_id: number;
  gross_amount: number;
  net_amount: number;
  points_earned: number;
  method: string;
  note: string | null;
  receipt_code: string | null;
  created_at: string;
}

export interface TransactionWithMemberResponse {
  transaction: TransactionResponse;
  member_phone: string | null;
  member_full_name: string | null;
  new_balance: number;
  new_total_earned: number;
  new_tier_id: number | null;
  new_tier_name: string | null;
  tier_upgraded: boolean;
}

export interface CreateManualTransactionRequest {
  phone: string;
  gross_amount: number;
  note?: string | null;
  receipt_code?: string | null;
}

// C4: List/detail/update cho /partner/transactions
export interface TransactionListItem {
  id: number;
  created_at: string;
  receipt_code: string | null;
  membership_display_name: string;
  gross_amount: number;
  net_amount: number;
  points_earned: number;
  method: string;
}

export interface TransactionListResponse {
  items: TransactionListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface TransactionDetailResponse extends TransactionListItem {
  note: string | null;
}

export interface TransactionUpdateRequest {
  receipt_code?: string | null;
  note?: string | null;
}

// Analytics dashboard (match backend schemas/analytics.py)
export interface DailyTransactionPoint {
  day: string;
  transaction_count: number;
  total_revenue: number;
  total_points_earned: number;
}

export interface TierDistributionPoint {
  tier_id: number | null;
  tier_name: string;
  member_count: number;
}

export interface DashboardResponse {
  period_from: string;
  period_to: string;
  member_count: number;
  transaction_count: number;
  total_revenue: number;
  total_redemption_count: number;
  redemption_rate: number;
  daily_transactions: DailyTransactionPoint[];
  tier_distribution: TierDistributionPoint[];
}

// Tiers
export interface TierResponse {
  id: number;
  partner_id: number;
  name: string;
  min_points: number;
  earn_multiplier: string; // Decimal serialised as string by backend
  perks: Record<string, unknown>;
  is_active: boolean;
}

export interface TierUpdateRequest {
  name?: string;
  min_points?: number;
  earn_multiplier?: string;
  perks?: Record<string, unknown>;
  is_active?: boolean;
}

// Point Rules
export interface PointRuleResponse {
  id: number;
  partner_id: number;
  points_per_unit: string; // Decimal serialised as string
  unit_amount: number;
  min_amount: number;
  use_tiers: boolean;
  is_active: boolean;
  created_at: string;
}

export interface PointRuleUpdateRequest {
  points_per_unit?: string;
  unit_amount?: number;
  min_amount?: number;
  use_tiers?: boolean;
  is_active?: boolean;
}

// Settings
export interface PartnerSettings {
  points_on_gross: boolean;
  signup_bonus_points: number;
  redemption_default_ttl_days: number;
  default_tier_id: number | null;
}

// Ledger
export interface LedgerEntryResponse {
  id: number;
  tenant_id: number;
  membership_id: number;
  delta: number;
  reason: string;
  ref_type: string;
  ref_id: number | null;
  balance_after: number;
  description: string | null;
  created_at: string;
}

// Admin
export interface PlatformStatsResponse {
  total_tenants: number;
  total_users: number;
  total_transactions: number;
  total_points_circulating: number;
}

export interface LoginLogItem {
  id: number;
  user_id: number | null;
  identifier: string;
  ip: string;
  user_agent: string | null;
  success: boolean;
  failure_reason: string | null;
  created_at: string;
  user_email: string | null;
}

export interface LoginLogListResponse {
  items: LoginLogItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface PointAdjustmentItem {
  id: number;
  user_id: number;
  user_email: string | null;
  partner_id: number;
  partner_name: string | null;
  actor_user_id: number | null;
  actor_email: string | null;
  delta: number;
  balance_after: number;
  description: string | null;
  created_at: string;
}

export interface PointAdjustmentListResponse {
  items: PointAdjustmentItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface PartnerEarnedItem {
  partner_id: number;
  name: string;
  total_earned: number;
}

export interface PointsSummaryResponse {
  total_circulating: number;
  total_earned: number;
  total_redeemed: number;
  total_adjusted: number;
  by_partner: PartnerEarnedItem[];
}

export interface PartnerDetailResponse {
  id: number;
  name: string;
  slug: string;
  status: string;
  category: string;
  description: string | null;
  logo_url: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  address: string | null;
  tax_code: string | null;
  website: string | null;
  business_hours: string | null;
  created_at: string;
  activated_at: string | null;
  owner_id: number;
  owner_name: string | null;
  owner_email: string | null;
  owner_phone: string | null;
  member_count: number;
  active_member_count: number;
  transaction_count: number;
  total_revenue: number;
  redemption_count: number;
  reward_count: number;
}

export interface AdminPartnerListRow {
  id: number;
  name: string;
  slug: string;
  status: string;
  category: string;
  logo_url: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  created_at: string;
  activated_at: string | null;
  owner_id: number;
  owner_name: string | null;
  owner_email: string | null;
  active_member_count: number;
  active_member_count_30d: number;
}

export interface AdminPartnerStaffRow {
  user_id: number;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  role: string;
  added_at: string;
  is_active: boolean;
}

export interface AdminPartnerMemberRow {
  membership_id: number;
  user_id: number;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  points_balance: number;
  total_points_earned: number;
  current_tier_name: string | null;
  joined_at: string;
  archived: boolean;
}

export interface AdminUserRow {
  id: number;
  email: string | null;
  phone: string | null;
  full_name: string | null;
  system_role: "regular" | "admin" | "super_admin";
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminUserListResponse {
  total: number;
  items: AdminUserRow[];
}

export interface AdminMembershipInfo {
  tenant_id: number;
  tenant_name: string;
  tenant_slug: string;
  points_balance: number;
  total_points_earned: number;
  current_tier_name: string | null;
  joined_at: string;
  archived: boolean;
}

export interface AdminUserDetailResponse extends AdminUserRow {
  memberships: AdminMembershipInfo[];
}

export interface AdminUserUpdateRequest {
  is_active?: boolean;
  system_role?: "regular" | "admin" | "super_admin";
}

export interface AdminResetPasswordResponse {
  user_id: number;
  temporary_password: string;
}

export interface AuditFeedItem {
  event_type:
    | "tenant_created"
    | "tenant_approved"
    | "tenant_suspended"
    | "user_registered"
    | "transaction";
  title: string;
  description: string;
  at: string;
  tenant_name: string | null;
}

export interface AdminSettingsResponse {
  environment: string;
  debug: boolean;
  jwt_expire_minutes: number;
  refresh_expire_days: number;
  scheduler_enabled: boolean;
  allowed_origins: string[];
  app_name: string;
}
