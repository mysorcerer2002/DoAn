import { api } from "@/lib/api";
import type {
  AuthorizationOtpResponse,
  AuthorizationSignResponse,
  CampaignEnrollPreview,
  CampaignServiceFee,
  CampaignTemplatePublic,
  EnrollFormInput,
  TenantAuthorizationDetail,
  TenantAuthorizationSummary,
} from "@/types/merchant-enroll";

// ==================== Enrollment ====================

export const enrollmentApi = {
  listTemplates: () =>
    api.get<CampaignTemplatePublic[]>("/merchant/campaign-templates"),

  preview: (form: EnrollFormInput) =>
    api.post<CampaignEnrollPreview>("/merchant/campaigns/enroll/preview", form),

  requestOtp: (form: EnrollFormInput) =>
    api.post<AuthorizationOtpResponse>("/merchant/authorizations/request-otp", {
      form,
    }),

  sign: (form: EnrollFormInput, otp_code: string, consent_checked: boolean) =>
    api.post<AuthorizationSignResponse>("/merchant/authorizations/sign", {
      form,
      otp_code,
      consent_checked,
    }),
};

// ==================== Authorizations ====================

export const authorizationsApi = {
  list: () =>
    api.get<TenantAuthorizationSummary[]>("/merchant/authorizations"),

  get: (id: number) =>
    api.get<TenantAuthorizationDetail>(`/merchant/authorizations/${id}`),

  revoke: (id: number, reason?: string) =>
    api.post<TenantAuthorizationDetail>(
      `/merchant/authorizations/${id}/revoke`,
      { reason: reason ?? null },
    ),
};

// ==================== Campaign service fees ====================

export const campaignFeesApi = {
  listForCampaign: (campaignId: number) =>
    api.get<CampaignServiceFee[]>(
      `/merchant/campaigns/${campaignId}/service-fees`,
    ),
};
