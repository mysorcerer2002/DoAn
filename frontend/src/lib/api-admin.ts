import { api } from "@/lib/api";
import type {
  AdminCampaignDetailResponse,
  ApprovalEventRow,
  CampaignTemplateCreateRequest,
  CampaignTemplateResponse,
  CampaignTemplateUpdateRequest,
  OverdueReportRow,
  PendingCampaignRow,
  RejectCampaignRequest,
  RegulatorySubmissionRequest,
  RegulatorySubmissionResponse,
} from "@/types/admin";

// ==================== Campaign Templates ====================
export const campaignTemplatesApi = {
  list: (params?: { source?: string; is_active?: boolean; include_deleted?: boolean }) =>
    api.get<CampaignTemplateResponse[]>("/admin/campaign-templates", { params }),

  create: (data: CampaignTemplateCreateRequest) =>
    api.post<CampaignTemplateResponse>("/admin/campaign-templates", data),

  get: (id: number) =>
    api.get<CampaignTemplateResponse>(`/admin/campaign-templates/${id}`),

  update: (id: number, data: CampaignTemplateUpdateRequest) =>
    api.patch<CampaignTemplateResponse>(`/admin/campaign-templates/${id}`, data),

  softDelete: (id: number) =>
    api.delete<CampaignTemplateResponse>(`/admin/campaign-templates/${id}`),
};

// ==================== Admin Campaign Approval ====================
export const adminCampaignsApi = {
  listPending: (params?: { limit?: number; offset?: number }) =>
    api.get<PendingCampaignRow[]>("/admin/campaigns/pending", { params }),

  listOverdue: (params?: { limit?: number }) =>
    api.get<OverdueReportRow[]>("/admin/campaigns/overdue-reports", { params }),

  getDetail: (id: number) =>
    api.get<AdminCampaignDetailResponse>(`/admin/campaigns/${id}`),

  listEvents: (id: number) =>
    api.get<ApprovalEventRow[]>(`/admin/campaigns/${id}/events`),

  markOpsStarted: (id: number) =>
    api.post<AdminCampaignDetailResponse>(`/admin/campaigns/${id}/mark-ops-started`),

  addRegulatorySubmission: (id: number, data: RegulatorySubmissionRequest) =>
    api.post<RegulatorySubmissionResponse>(
      `/admin/campaigns/${id}/regulatory-submissions`,
      data
    ),

  approve: (id: number) =>
    api.post<AdminCampaignDetailResponse>(`/admin/campaigns/${id}/approve`),

  reject: (id: number, data: RejectCampaignRequest) =>
    api.post<AdminCampaignDetailResponse>(`/admin/campaigns/${id}/reject`, data),
};
