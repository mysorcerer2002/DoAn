"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, CheckCircle, XCircle, FileText, Clock } from "lucide-react";

import {
  useAdminCampaignDetail,
  useCampaignEvents,
  useMarkOpsStarted,
  useAddRegulatorySubmission,
  useApproveCampaign,
  useRejectCampaign,
} from "@/lib/hooks/use-admin-campaigns";
import type { RegulatorySubmissionRequest, RejectCampaignRequest } from "@/types/admin";

const STATUS_LABELS: Record<string, string> = {
  pending: "Chờ duyệt",
  auto_approved: "Tự động duyệt",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  draft: "Nháp",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  auto_approved: "bg-emerald-100 text-emerald-700",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-red-100 text-red-600",
  draft: "bg-slate-100 text-slate-600",
};

const TIER_LABELS: Record<string, string> = {
  none: "Không cần",
  auto: "Tự động",
  notify: "Thông báo",
  register: "Đăng ký",
  reject: "Từ chối",
};

const FEE_LABELS: Record<string, string> = {
  none: "Không áp dụng",
  pending: "Chờ thanh toán",
  paid: "Đã thanh toán",
  waived: "Miễn phí",
};

const PROGRAM_FORM_LABELS: Record<string, string> = {
  giam_gia: "Giảm giá",
  tang_kem: "Tặng kèm",
  may_rui_quay_so: "May rủi – quay số",
  may_rui_truc_tiep: "May rủi – trực tiếp",
  khach_hang_thuong_xuyen: "Khách hàng thường xuyên",
};

const DOC_TYPE_LABELS: Record<string, string> = {
  notify_so_ct: "Thông báo Sở CT",
  dang_ky_so_ct: "Đăng ký Sở CT",
  dieu_le: "Điều lệ",
  du_toan: "Dự toán",
  xac_nhan_so_ct: "Xác nhận Sở CT",
  bao_cao_ket_thuc: "Báo cáo kết thúc",
};

const EVENT_TYPE_COLORS: Record<string, string> = {
  created: "bg-slate-100 text-slate-600",
  submitted: "bg-blue-100 text-blue-700",
  ops_started: "bg-indigo-100 text-indigo-700",
  regulatory_submission: "bg-violet-100 text-violet-700",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-red-100 text-red-600",
  post_report_filed: "bg-teal-100 text-teal-700",
};

function fmtMoney(n: number): string {
  return n.toLocaleString("vi-VN") + "₫";
}

function fmtDatetime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

const EMPTY_SUBMISSION: RegulatorySubmissionRequest = {
  doc_type: "notify_so_ct",
  reference_no: "",
  url: "",
  note: "",
  submitted_at: "",
};

export default function AdminCampaignDetailPage() {
  const { id: rawId } = useParams<{ id: string }>();
  const campaignId = Number(rawId);
  const router = useRouter();

  const { data: campaign, isLoading } = useAdminCampaignDetail(campaignId);
  const { data: events = [] } = useCampaignEvents(campaignId);

  const markOpsStartedMut = useMarkOpsStarted();
  const addSubmissionMut = useAddRegulatorySubmission();
  const approveMut = useApproveCampaign();
  const rejectMut = useRejectCampaign();

  const [subForm, setSubForm] = useState<RegulatorySubmissionRequest>(EMPTY_SUBMISSION);
  const [subError, setSubError] = useState<string | null>(null);
  const [subSuccess, setSubSuccess] = useState(false);

  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectForm, setRejectForm] = useState<RejectCampaignRequest>({
    reason: "",
    acknowledge_used_vouchers: false,
  });
  const [rejectError, setRejectError] = useState<string | null>(null);
  const [rejectUsedCount, setRejectUsedCount] = useState<number | null>(null);

  const [actionError, setActionError] = useState<string | null>(null);

  async function handleMarkOpsStarted() {
    setActionError(null);
    try {
      await markOpsStartedMut.mutateAsync(campaignId);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionError(msg ?? "Lỗi khi cập nhật.");
    }
  }

  async function handleAddSubmission() {
    setSubError(null);
    setSubSuccess(false);
    if (!subForm.doc_type) { setSubError("Vui lòng chọn loại hồ sơ."); return; }
    try {
      // Pydantic datetime | None không parse chuỗi rỗng — chuyển "" → null
      // cho submitted_at và các field text optional.
      const payload: RegulatorySubmissionRequest = {
        doc_type: subForm.doc_type,
        reference_no: subForm.reference_no?.trim() ? subForm.reference_no : null,
        url: subForm.url?.trim() ? subForm.url : null,
        note: subForm.note?.trim() ? subForm.note : null,
        submitted_at: subForm.submitted_at?.trim() ? subForm.submitted_at : null,
      };
      await addSubmissionMut.mutateAsync({ id: campaignId, data: payload });
      setSubForm(EMPTY_SUBMISSION);
      setSubSuccess(true);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setSubError(msg ?? "Lỗi khi thêm hồ sơ.");
    }
  }

  async function handleApprove() {
    setActionError(null);
    try {
      await approveMut.mutateAsync(campaignId);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionError(msg ?? "Lỗi khi duyệt.");
    }
  }

  async function handleReject() {
    setRejectError(null);
    setRejectUsedCount(null);
    if (!rejectForm.reason.trim() || rejectForm.reason.trim().length < 3) {
      setRejectError("Lý do tối thiểu 3 ký tự.");
      return;
    }
    try {
      await rejectMut.mutateAsync({ id: campaignId, data: rejectForm });
      setRejectModalOpen(false);
    } catch (e: unknown) {
      const err = e as {
        response?: {
          status?: number;
          data?: { code?: string; message?: string; used_count?: number; detail?: string };
        };
      };
      if (err.response?.status === 409 && err.response.data?.code === "USED_VOUCHERS_REQUIRE_ACK") {
        setRejectUsedCount(err.response.data.used_count ?? null);
        setRejectError(err.response.data.message ?? "Có voucher đã sử dụng. Vui lòng xác nhận.");
        // Auto-tick để user chỉ cần bấm lại Từ chối.
        setRejectForm((p) => ({ ...p, acknowledge_used_vouchers: true }));
      } else {
        setRejectError(err.response?.data?.detail ?? "Lỗi khi từ chối.");
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="text-slate-400">Đang tải...</span>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <span className="text-slate-500">Không tìm thấy chiến dịch.</span>
        <button
          type="button"
          onClick={() => router.back()}
          className="text-sm text-indigo-600 underline"
        >
          Quay lại
        </button>
      </div>
    );
  }

  const canMarkOps =
    !campaign.ops_filing_started_at && campaign.approval_status === "pending";
  const canApprove =
    campaign.approval_status === "pending";
  const canReject =
    campaign.approval_status === "pending" || campaign.approval_status === "approved";

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => router.back()}
          className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-800">{campaign.name}</h1>
          <p className="text-sm text-slate-500">#{campaign.id} · {campaign.tenant_id}</p>
        </div>
        <span
          className={`ml-auto rounded-full px-3 py-1 text-[12px] font-bold ${STATUS_COLORS[campaign.approval_status] ?? "bg-slate-100 text-slate-600"}`}
        >
          {STATUS_LABELS[campaign.approval_status] ?? campaign.approval_status}
        </span>
      </div>

      {actionError && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{actionError}</div>
      )}

      {/* Section 1: Thông tin chung */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-sm font-bold text-slate-700 uppercase tracking-wide">
          Thông tin chung
        </h2>
        <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <InfoRow label="Hình thức" value={PROGRAM_FORM_LABELS[campaign.program_form] ?? campaign.program_form} />
          <InfoRow label="Mức duyệt" value={TIER_LABELS[campaign.approval_tier] ?? campaign.approval_tier} />
          <InfoRow label="Dự toán" value={fmtMoney(campaign.estimated_cost)} />
          <InfoRow label="Chi thực" value={fmtMoney(campaign.realized_cost)} />
          <InfoRow label="Bắt đầu" value={fmtDate(campaign.starts_at)} />
          <InfoRow label="Kết thúc" value={fmtDate(campaign.ends_at)} />
          <InfoRow label="Hạn báo cáo" value={fmtDate(campaign.post_report_due_at)} />
          <InfoRow label="Ngày tạo" value={fmtDatetime(campaign.created_at)} />
          {campaign.rejection_reason && (
            <div className="col-span-2 rounded-lg bg-red-50 px-3 py-2 text-red-700">
              <span className="font-semibold">Lý do từ chối: </span>
              {campaign.rejection_reason}
            </div>
          )}
        </div>
      </section>

      {/* Section 2: Uỷ quyền */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-bold text-slate-700 uppercase tracking-wide">
          Uỷ quyền
        </h2>
        <p className="text-sm text-slate-600">
          {campaign.authorization_id ? (
            <span>
              Mã uỷ quyền:{" "}
              <span className="font-mono font-semibold text-slate-800">
                #{campaign.authorization_id}
              </span>
            </span>
          ) : (
            <span className="text-slate-400">Chưa có uỷ quyền.</span>
          )}
        </p>
      </section>

      {/* Section 3: Phí dịch vụ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-bold text-slate-700 uppercase tracking-wide">
          Phí dịch vụ
        </h2>
        <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <InfoRow label="Tổng phí" value={fmtMoney(campaign.service_fee_total)} />
          <InfoRow
            label="Trạng thái phí"
            value={FEE_LABELS[campaign.service_fee_status] ?? campaign.service_fee_status}
          />
        </div>
      </section>

      {/* Section 4: Hồ sơ pháp lý */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wide">
          Hồ sơ pháp lý
        </h2>

        <div className="flex items-center gap-4">
          <div className="text-sm">
            <span className="text-slate-500">Ops bắt đầu: </span>
            <span className="font-medium text-slate-700">
              {fmtDatetime(campaign.ops_filing_started_at)}
            </span>
          </div>
          {canMarkOps && (
            <button
              type="button"
              onClick={handleMarkOpsStarted}
              disabled={markOpsStartedMut.isPending}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {markOpsStartedMut.isPending ? "Đang cập nhật..." : "Đánh dấu ops bắt đầu"}
            </button>
          )}
        </div>

        {campaign.post_report_submitted_at && (
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-700">Báo cáo kết thúc: </span>
            {fmtDatetime(campaign.post_report_submitted_at)}
          </p>
        )}

        {/* Add regulatory submission form */}
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-4 space-y-3">
          <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
            Thêm hồ sơ nộp
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Loại hồ sơ</label>
              <select
                value={subForm.doc_type}
                onChange={(e) => setSubForm((p) => ({ ...p, doc_type: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
              >
                {Object.entries(DOC_TYPE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Số tham chiếu
              </label>
              <input
                value={subForm.reference_no ?? ""}
                onChange={(e) => setSubForm((p) => ({ ...p, reference_no: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
                placeholder="Số công văn, quyết định..."
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">URL hồ sơ</label>
              <input
                value={subForm.url ?? ""}
                onChange={(e) => setSubForm((p) => ({ ...p, url: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
                placeholder="https://..."
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Ngày nộp
              </label>
              <input
                type="datetime-local"
                value={subForm.submitted_at ?? ""}
                onChange={(e) => setSubForm((p) => ({ ...p, submitted_at: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Ghi chú</label>
            <textarea
              value={subForm.note ?? ""}
              onChange={(e) => setSubForm((p) => ({ ...p, note: e.target.value }))}
              rows={2}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm"
            />
          </div>
          {subError && <p className="text-xs text-red-600">{subError}</p>}
          {subSuccess && (
            <p className="text-xs text-emerald-600">Thêm hồ sơ thành công.</p>
          )}
          <button
            type="button"
            onClick={handleAddSubmission}
            disabled={addSubmissionMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <FileText className="h-3.5 w-3.5" />
            {addSubmissionMut.isPending ? "Đang lưu..." : "Thêm hồ sơ"}
          </button>
        </div>
      </section>

      {/* Section 5: Nhật ký audit */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-sm font-bold text-slate-700 uppercase tracking-wide">
          Nhật ký audit
        </h2>
        {events.length === 0 ? (
          <p className="text-sm text-slate-400">Chưa có sự kiện nào.</p>
        ) : (
          <div className="space-y-2">
            {events.map((ev) => (
              <div
                key={ev.id}
                className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5"
              >
                <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${EVENT_TYPE_COLORS[ev.event_type] ?? "bg-slate-100 text-slate-600"}`}
                    >
                      {ev.event_type}
                    </span>
                    {ev.actor_user_id && (
                      <span className="text-xs text-slate-500">
                        bởi user #{ev.actor_user_id}
                      </span>
                    )}
                    <span className="ml-auto text-[11px] text-slate-400">
                      {fmtDatetime(ev.at)}
                    </span>
                  </div>
                  {ev.reason && (
                    <p className="mt-1 text-xs text-slate-600">{ev.reason}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Action buttons */}
      <div className="flex gap-4 pt-2">
        <button
          type="button"
          onClick={handleApprove}
          disabled={!canApprove || approveMut.isPending}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <CheckCircle className="h-5 w-5" />
          {approveMut.isPending ? "Đang duyệt..." : "Duyệt"}
        </button>
        <button
          type="button"
          onClick={() => { setRejectModalOpen(true); setRejectError(null); setRejectUsedCount(null); }}
          disabled={!canReject || rejectMut.isPending}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-red-600 px-6 py-3 font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <XCircle className="h-5 w-5" />
          Từ chối
        </button>
      </div>

      {/* Reject modal */}
      {rejectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-base font-bold text-slate-800">Từ chối chiến dịch</h2>

            {rejectUsedCount != null && (
              <div className="mb-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-700">
                Có <strong>{rejectUsedCount} voucher</strong> đã được sử dụng. Các voucher này sẽ không bị huỷ nhưng bạn cần xác nhận.
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">
                  Lý do từ chối *
                </label>
                <textarea
                  value={rejectForm.reason}
                  onChange={(e) =>
                    setRejectForm((p) => ({ ...p, reason: e.target.value }))
                  }
                  rows={3}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  placeholder="Nhập lý do..."
                />
              </div>
              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={rejectForm.acknowledge_used_vouchers}
                  onChange={(e) =>
                    setRejectForm((p) => ({
                      ...p,
                      acknowledge_used_vouchers: e.target.checked,
                    }))
                  }
                  className="mt-0.5 h-4 w-4 rounded"
                />
                <span className="text-slate-600">
                  Tôi xác nhận đã biết có voucher đã sử dụng và đồng ý tiến hành từ chối.
                </span>
              </label>
              {rejectError && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
                  {rejectError}
                </p>
              )}
            </div>

            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setRejectModalOpen(false)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={handleReject}
                disabled={rejectMut.isPending}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {rejectMut.isPending ? "Đang xử lý..." : "Xác nhận từ chối"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-slate-500">{label}: </span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}
