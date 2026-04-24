import { api } from "@/lib/api";
import type {
  AuthorizationOtpResponse,
  AuthorizationSignResponse,
  CampaignEnrollPreview,
  CampaignTemplatePublic,
  EnrollFormInput,
  PartnerAuthorizationDetail,
  PartnerAuthorizationSummary,
} from "@/types/partner-enroll";

// ==================== Enrollment ====================

export const enrollmentApi = {
  listTemplates: () =>
    api.get<CampaignTemplatePublic[]>("/partner/campaign-templates"),

  preview: (form: EnrollFormInput) =>
    api.post<CampaignEnrollPreview>("/partner/campaigns/enroll/preview", form),

  requestOtp: (form: EnrollFormInput) =>
    api.post<AuthorizationOtpResponse>("/partner/authorizations/request-otp", {
      form,
    }),

  sign: (form: EnrollFormInput, otp_code: string, consent_checked: boolean) =>
    api.post<AuthorizationSignResponse>("/partner/authorizations/sign", {
      form,
      otp_code,
      consent_checked,
    }),
};

// ==================== Authorizations ====================

export const authorizationsApi = {
  list: () =>
    api.get<PartnerAuthorizationSummary[]>("/partner/authorizations"),

  get: (id: number) =>
    api.get<PartnerAuthorizationDetail>(`/partner/authorizations/${id}`),

  revoke: (id: number, reason?: string) =>
    api.post<PartnerAuthorizationDetail>(
      `/partner/authorizations/${id}/revoke`,
      { reason: reason ?? null },
    ),
};

