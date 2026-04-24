// Types cho flow enroll campaign managed-service — Phase 14
// Mirror Pydantic DTOs từ backend/app/schemas/campaign_enrollment.py
// và backend/app/schemas/tenant_authorization.py

// ==================== Templates ====================

export interface CampaignTemplatePublic {
  id: number;
  code: string;
  name: string;
  description: string | null;
  source: string;
  program_form: string;
  discount_type: string; // "percent" | "fixed"
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
}

// ==================== Enroll form ====================

export interface EnrollFormInput {
  template_id: number;
  name: string;
  description?: string | null;
  terms?: string | null;
  usage_guide?: string | null;
  support_contact?: string | null;
  discount_value: number;
  min_order: number;
  max_discount?: number | null;
  target_tier_id?: number | null;
  max_issuances?: number | null;
  starts_at: string; // ISO datetime string
  ends_at: string;   // ISO datetime string
}

// ==================== Preview ====================

export interface CampaignEnrollPreview {
  template_id: number;
  template_version: number;
  program_form: string;
  approval_tier: string;
  estimated_cost: number;
  auth_doc_text: string;
  auth_doc_hash: string;
  consent_text_version: string;
}

// ==================== OTP ====================

export interface AuthorizationOtpRequest {
  form: EnrollFormInput;
}

export interface AuthorizationOtpResponse {
  email_masked: string;
  ttl_minutes: number;
  dev_code?: string | null;
}

// ==================== Sign ====================

export interface AuthorizationSignRequest {
  form: EnrollFormInput;
  otp_code: string;
  consent_checked: boolean;
}

export interface AuthorizationSignResponse {
  campaign_id: number;
  authorization_id: number;
  approval_status: string;
  approval_tier: string;
}

// ==================== Authorization list/detail ====================

export interface PartnerAuthorizationSummary {
  id: number;
  scope: string;
  campaign_id: number | null;
  document_content_hash: string;
  signed_at: string;
  signature_method: string;
  valid_from: string;
  valid_until: string;
  revoked_at: string | null;
  revoked_reason: string | null;
}

export interface SignaturePayloadPublic {
  ip?: string | null;
  user_agent?: string | null;
  otp_purpose?: string | null;
  consent_text_version?: string | null;
  consent_text_hash?: string | null;
  doc_hash?: string | null;
  template_version?: number | null;
  signed_at_server?: string | null;
  signed_at_client?: string | null;
  session_id?: string | null;
  otp_delivery_address?: string | null;
  otp_attempts_count?: number | null;
  rendered_pdf_hash?: string | null;
}

export interface PartnerAuthorizationDetail {
  id: number;
  tenant_id: number;
  scope: string;
  campaign_id: number | null;
  document_content_hash: string;
  document_url: string | null;
  signed_by_user_id: number;
  signed_at: string;
  signature_method: string;
  signature_payload: SignaturePayloadPublic;
  valid_from: string;
  valid_until: string;
  revoked_at: string | null;
  revoked_reason: string | null;
  retention_until: string;
}

