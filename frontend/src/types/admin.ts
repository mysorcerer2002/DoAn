/** TypeScript types cho admin campaign approval + template workflow. */

export interface CampaignTemplateResponse {
  id: number;
  code: string;
  name: string;
  description: string | null;
  source: string; // manual | ext_merchant | ext_platform
  program_form: string;
  discount_type: string; // percent | fixed
  default_usage_guide: string | null;
  default_support_contact: string | null;
  default_terms: string | null;
  max_discount_percent_cap: number | null;
  max_discount_value_cap: number | null;
  max_discount_fixed_cap: number | null;
  min_order_floor: number;
  max_issuances_cap: number | null;
  max_duration_days: number | null;
  min_voucher_ttl_days: number;
  max_voucher_ttl_days: number;
  version: number;
  is_active: boolean;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignTemplateCreateRequest {
  code: string;
  name: string;
  description?: string | null;
  source: string;
  program_form: string;
  discount_type: string;
  default_usage_guide?: string | null;
  default_support_contact?: string | null;
  default_terms?: string | null;
  max_discount_percent_cap?: number | null;
  max_discount_value_cap?: number | null;
  max_discount_fixed_cap?: number | null;
  min_order_floor?: number;
  max_issuances_cap?: number | null;
  max_duration_days?: number | null;
  min_voucher_ttl_days?: number;
  max_voucher_ttl_days?: number;
  is_active?: boolean;
}

export interface CampaignTemplateUpdateRequest {
  name?: string | null;
  description?: string | null;
  program_form?: string | null;
  discount_type?: string | null;
  default_usage_guide?: string | null;
  default_support_contact?: string | null;
  default_terms?: string | null;
  max_discount_percent_cap?: number | null;
  max_discount_value_cap?: number | null;
  max_discount_fixed_cap?: number | null;
  min_order_floor?: number | null;
  max_issuances_cap?: number | null;
  max_duration_days?: number | null;
  min_voucher_ttl_days?: number | null;
  max_voucher_ttl_days?: number | null;
  is_active?: boolean | null;
}

export interface PendingCampaignRow {
  id: number;
  tenant_id: number;
  tenant_name: string;
  name: string;
  program_form: string;
  approval_status: string; // pending | auto_approved | approved | rejected | draft
  approval_tier: string; // none | notify_so_ct | dang_ky_so_ct | full_dossier
  estimated_cost: number;
  starts_at: string;
  ends_at: string;
  authorization_id: number | null;
  ops_filing_started_at: string | null;
  created_at: string;
}

export interface AdminCampaignDetailResponse {
  id: number;
  tenant_id: number;
  name: string;
  description: string | null;
  program_form: string;
  approval_status: string;
  approval_tier: string;
  estimated_cost: number;
  realized_cost: number;
  starts_at: string;
  ends_at: string;
  authorization_id: number | null;
  ops_filing_started_at: string | null;
  post_report_due_at: string | null;
  post_report_submitted_at: string | null;
  reviewed_at: string | null;
  reviewed_by_user_id: number | null;
  rejection_reason: string | null;
  created_at: string;
}

export interface ApprovalEventRow {
  id: number;
  campaign_id: number;
  event_type: string;
  actor_user_id: number | null;
  reason: string | null;
  at: string;
}

export interface OverdueReportRow {
  id: number;
  tenant_id: number;
  tenant_name: string;
  name: string;
  approval_tier: string;
  ends_at: string;
  post_report_due_at: string;
  days_overdue: number;
}

export interface RegulatorySubmissionRequest {
  doc_type: string; // notify_so_ct | dang_ky_so_ct | dieu_le | du_toan | xac_nhan_so_ct | bao_cao_ket_thuc
  reference_no?: string | null;
  url?: string | null;
  note?: string | null;
  submitted_at?: string | null;
}

export interface RegulatorySubmissionResponse {
  id: number;
  campaign_id: number;
  doc_type: string;
  reference_no: string | null;
  url: string | null;
  note: string | null;
  submitted_at: string;
  submitted_by_user_id: number;
}

export interface RejectCampaignRequest {
  reason: string;
  acknowledge_used_vouchers: boolean;
}
