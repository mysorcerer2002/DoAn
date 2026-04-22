"use client";

import { AlertTriangle, Check, ChevronLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  useEnrollPreview,
  useEnrollTemplates,
  useRequestEnrollOtp,
  useSignEnroll,
} from "@/lib/hooks/use-merchant-enroll";
import type {
  CampaignEnrollPreview,
  CampaignTemplatePublic,
  EnrollFormInput,
} from "@/types/merchant-enroll";

// ==================== Helpers ====================

const PROGRAM_FORM_LABEL: Record<string, string> = {
  giam_gia: "Giảm giá",
  tang_kem: "Tặng kèm",
  may_rui_quay_so: "May rủi - Quay số",
  may_rui_truc_tiep: "May rủi - Trực tiếp",
  khach_hang_thuong_xuyen: "Khách hàng thường xuyên",
};

const APPROVAL_TIER_LABEL: Record<string, string> = {
  none: "Không cần duyệt",
  auto: "Tự động duyệt",
  notify: "Thông báo",
  register: "Cần đăng ký Sở CT",
  reject: "Từ chối",
};

const APPROVAL_STATUS_LABEL: Record<string, string> = {
  pending: "Đang chờ duyệt",
  auto_approved: "Đã duyệt tự động",
  approved: "Đã duyệt",
  rejected: "Bị từ chối",
  draft: "Nháp",
};

function formatMoney(n: number): string {
  return `${n.toLocaleString("vi-VN")}₫`;
}

function todayDateStr(): string {
  const d = new Date();
  d.setSeconds(0, 0);
  return d.toISOString().slice(0, 16);
}

// ==================== Sub-components ====================

function inputCls(hasError: boolean): string {
  return `mt-1 w-full rounded-xl border ${
    hasError ? "border-red-400" : "border-slate-200"
  } bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20`;
}

function FieldGroup({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-[12px] font-medium text-slate-500">{label}</label>
      {children}
      {error && <p className="mt-0.5 text-[11px] text-red-600">{error}</p>}
    </div>
  );
}

// ----- Step 1: Chọn template -----

function StepSelectTemplate({
  onSelect,
}: {
  onSelect: (t: CampaignTemplatePublic) => void;
}) {
  const { data: templates, isLoading, isError } = useEnrollTemplates();

  if (isLoading)
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </div>
    );
  if (isError || !templates)
    return (
      <p className="py-8 text-center text-red-600">
        Không tải được danh sách template
      </p>
    );

  return (
    <div className="space-y-4">
      <p className="text-[13px] text-slate-500">
        Chọn template chiến dịch do công ty định nghĩa. Bạn sẽ điền các thông
        tin chi tiết ở bước tiếp theo.
      </p>
      {templates.length === 0 && (
        <p className="py-8 text-center text-[13px] text-slate-400">
          Hiện chưa có template nào khả dụng.
        </p>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        {templates.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onSelect(t)}
            className="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-brand-indigo hover:shadow-md"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-headline text-[15px] font-bold text-slate-800 group-hover:text-brand-indigo">
                  {t.name}
                </p>
                <p className="mt-0.5 text-[11px] text-slate-400">{t.code}</p>
              </div>
              <span className="shrink-0 rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-medium text-brand-indigo">
                {PROGRAM_FORM_LABEL[t.program_form] ?? t.program_form}
              </span>
            </div>
            {t.description && (
              <p className="mt-2 line-clamp-2 text-[12px] text-slate-600">
                {t.description}
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
              <span className="rounded-full bg-slate-100 px-2 py-0.5">
                {t.discount_type === "percent"
                  ? "Phần trăm %"
                  : "Số tiền cố định ₫"}
              </span>
              {t.min_order_floor > 0 && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5">
                  Đơn tối thiểu {formatMoney(t.min_order_floor)}
                </span>
              )}
              {t.max_duration_days && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5">
                  Tối đa {t.max_duration_days} ngày
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ----- Step 2: Fill form -----

interface FormState {
  name: string;
  description: string;
  terms: string;
  usage_guide: string;
  support_contact: string;
  discount_value: string;
  min_order: string;
  max_discount: string;
  max_issuances: string;
  starts_at: string;
  ends_at: string;
}

function StepFillForm({
  template,
  formState,
  onChange,
  onBack,
  onNext,
}: {
  template: CampaignTemplatePublic;
  formState: FormState;
  onChange: (f: FormState) => void;
  onBack: () => void;
  onNext: (input: EnrollFormInput, preview: CampaignEnrollPreview) => void;
}) {
  const previewMutation = useEnrollPreview();
  const [errors, setErrors] = useState<Record<string, string>>({});

  function set(key: keyof FormState, value: string) {
    onChange({ ...formState, [key]: value });
  }

  function validate(): boolean {
    const errs: Record<string, string> = {};
    const dv = Number(formState.discount_value);
    if (!formState.name.trim()) errs.name = "Nhập tên chiến dịch";
    if (!formState.discount_value || dv <= 0)
      errs.discount_value = "Giá trị giảm phải > 0";
    if (
      template.discount_type === "percent" &&
      template.max_discount_percent_cap &&
      dv > template.max_discount_percent_cap
    )
      errs.discount_value = `Không vượt quá ${template.max_discount_percent_cap}%`;
    if (
      template.discount_type === "fixed" &&
      template.max_discount_fixed_cap &&
      dv > template.max_discount_fixed_cap
    )
      errs.discount_value = `Không vượt cap ${formatMoney(template.max_discount_fixed_cap)}`;

    // Cap `max_discount` cho percent template — shop không được mở quá
    // `max_discount_value_cap` (absolute tiền tối đa 1 voucher).
    if (formState.max_discount) {
      const md = Number(formState.max_discount);
      if (md <= 0) errs.max_discount = "Giảm tối đa phải > 0";
      else if (
        template.discount_type === "percent" &&
        template.max_discount_value_cap &&
        md > template.max_discount_value_cap
      )
        errs.max_discount = `Vượt cap ${formatMoney(template.max_discount_value_cap)}`;
    }

    const mo = Number(formState.min_order || 0);
    if (mo < template.min_order_floor)
      errs.min_order = `Đơn tối thiểu phải >= ${formatMoney(template.min_order_floor)}`;

    const maxIss = formState.max_issuances
      ? Number(formState.max_issuances)
      : null;
    if (
      maxIss != null &&
      template.max_issuances_cap &&
      maxIss > template.max_issuances_cap
    )
      errs.max_issuances = `Tối đa ${template.max_issuances_cap} lượt phát`;

    if (!formState.starts_at) errs.starts_at = "Nhập ngày bắt đầu";
    if (!formState.ends_at) errs.ends_at = "Nhập ngày kết thúc";

    if (formState.starts_at && formState.ends_at) {
      const start = new Date(formState.starts_at);
      const end = new Date(formState.ends_at);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const startDay = new Date(start);
      startDay.setHours(0, 0, 0, 0);
      if (startDay < today)
        errs.starts_at = "Ngày bắt đầu không được trong quá khứ";
      if (end <= start)
        errs.ends_at = "Ngày kết thúc phải sau ngày bắt đầu";
      if (template.max_duration_days) {
        const diffDays =
          (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
        if (diffDays > template.max_duration_days)
          errs.ends_at = `Thời gian tối đa ${template.max_duration_days} ngày`;
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleNext() {
    if (!validate()) return;
    const input: EnrollFormInput = {
      template_id: template.id,
      name: formState.name.trim(),
      description: formState.description.trim() || null,
      terms: formState.terms.trim() || null,
      usage_guide: formState.usage_guide.trim() || null,
      support_contact: formState.support_contact.trim() || null,
      discount_value: Number(formState.discount_value),
      min_order: Number(formState.min_order || 0),
      max_discount: formState.max_discount
        ? Number(formState.max_discount)
        : null,
      max_issuances: formState.max_issuances
        ? Number(formState.max_issuances)
        : null,
      starts_at: new Date(formState.starts_at).toISOString(),
      ends_at: new Date(formState.ends_at).toISOString(),
    };
    try {
      const res = await previewMutation.mutateAsync(input);
      onNext(input, res.data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setErrors({
        _form:
          err.response?.data?.detail ?? "Lỗi khi xác nhận form với server",
      });
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-[12px] text-slate-400">
        Template:{" "}
        <span className="font-medium text-slate-700">{template.name}</span>
      </p>

      <FieldGroup label="Tên chiến dịch" error={errors.name}>
        <input
          type="text"
          value={formState.name}
          onChange={(e) => set("name", e.target.value)}
          className={inputCls(!!errors.name)}
        />
      </FieldGroup>

      <FieldGroup label="Mô tả (tuỳ chọn)">
        <textarea
          rows={2}
          value={formState.description}
          onChange={(e) => set("description", e.target.value)}
          className={inputCls(false)}
        />
      </FieldGroup>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <FieldGroup
          label={`Giá trị giảm (${template.discount_type === "percent" ? "%" : "₫"})`}
          error={errors.discount_value}
        >
          <input
            type="number"
            min="1"
            value={formState.discount_value}
            onChange={(e) => set("discount_value", e.target.value)}
            className={inputCls(!!errors.discount_value)}
          />
        </FieldGroup>

        <FieldGroup label="Đơn tối thiểu (₫)" error={errors.min_order}>
          <input
            type="number"
            min="0"
            value={formState.min_order}
            onChange={(e) => set("min_order", e.target.value)}
            className={inputCls(!!errors.min_order)}
          />
        </FieldGroup>

        {template.discount_type === "percent" && (
          <FieldGroup label="Giảm tối đa (₫, tuỳ chọn)">
            <input
              type="number"
              min="1"
              value={formState.max_discount}
              onChange={(e) => set("max_discount", e.target.value)}
              className={inputCls(false)}
            />
          </FieldGroup>
        )}

        <FieldGroup
          label="Số lượng phát tối đa"
          error={errors.max_issuances}
        >
          <input
            type="number"
            min="1"
            value={formState.max_issuances}
            onChange={(e) => set("max_issuances", e.target.value)}
            placeholder="Không giới hạn"
            className={inputCls(!!errors.max_issuances)}
          />
        </FieldGroup>

        <FieldGroup label="Bắt đầu" error={errors.starts_at}>
          <input
            type="datetime-local"
            value={formState.starts_at}
            onChange={(e) => set("starts_at", e.target.value)}
            min={todayDateStr()}
            className={inputCls(!!errors.starts_at)}
          />
        </FieldGroup>

        <FieldGroup label="Kết thúc" error={errors.ends_at}>
          <input
            type="datetime-local"
            value={formState.ends_at}
            onChange={(e) => set("ends_at", e.target.value)}
            className={inputCls(!!errors.ends_at)}
          />
        </FieldGroup>
      </div>

      <FieldGroup label="Điều khoản (tuỳ chọn)">
        <textarea
          rows={3}
          value={formState.terms}
          onChange={(e) => set("terms", e.target.value)}
          className={inputCls(false)}
        />
      </FieldGroup>

      <FieldGroup label="Hướng dẫn sử dụng (tuỳ chọn)">
        <textarea
          rows={2}
          value={formState.usage_guide}
          onChange={(e) => set("usage_guide", e.target.value)}
          className={inputCls(false)}
        />
      </FieldGroup>

      <FieldGroup label="Liên hệ hỗ trợ (tuỳ chọn)">
        <input
          type="text"
          value={formState.support_contact}
          onChange={(e) => set("support_contact", e.target.value)}
          className={inputCls(false)}
        />
      </FieldGroup>

      {errors._form && (
        <div className="rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {errors._form}
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 text-[13px] text-slate-500 hover:text-brand-indigo"
        >
          <ChevronLeft className="h-4 w-4" /> Quay lại
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={previewMutation.isPending}
          className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-60"
        >
          {previewMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Tiếp tục"
          )}
        </button>
      </div>
    </div>
  );
}

// ----- Step 3: Xác nhận uỷ quyền -----

function StepConfirm({
  preview,
  form,
  onBack,
  onOtpSent,
}: {
  preview: CampaignEnrollPreview;
  form: EnrollFormInput;
  onBack: () => void;
  onOtpSent: (
    emailMasked: string,
    ttlMinutes: number,
    devCode?: string | null,
  ) => void;
}) {
  const otpMutation = useRequestEnrollOtp();
  const [consentChecked, setConsentChecked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSendOtp() {
    setError(null);
    try {
      const res = await otpMutation.mutateAsync(form);
      onOtpSent(
        res.data.email_masked,
        res.data.ttl_minutes,
        res.data.dev_code,
      );
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? "Lỗi gửi OTP");
    }
  }

  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <h3 className="font-headline text-[14px] font-bold text-slate-800">
          Tóm tắt đăng ký
        </h3>
        <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
          <dt className="text-slate-400">Template</dt>
          <dd className="font-medium text-slate-700">
            #{preview.template_id} v{preview.template_version}
          </dd>
          <dt className="text-slate-400">Hình thức</dt>
          <dd className="font-medium text-slate-700">
            {PROGRAM_FORM_LABEL[preview.program_form] ?? preview.program_form}
          </dd>
          <dt className="text-slate-400">Mức duyệt</dt>
          <dd>
            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-bold text-brand-indigo">
              {APPROVAL_TIER_LABEL[preview.approval_tier] ??
                preview.approval_tier}
            </span>
          </dd>
          <dt className="text-slate-400">Chi phí ước tính</dt>
          <dd className="font-bold text-rose-600">
            {formatMoney(preview.estimated_cost)}
          </dd>
        </dl>
      </div>

      {/* Fees */}
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <h3 className="font-headline text-[14px] font-bold text-slate-800">
          Phí dịch vụ
        </h3>
        {!preview.service_fee_enabled ? (
          <p className="mt-2 text-[12px] italic text-slate-400">
            SERVICE_FEE_ENABLED=off (đồ án) — không áp dụng phí
          </p>
        ) : preview.fees.length === 0 ? (
          <p className="mt-2 text-[12px] text-slate-400">Không có phí.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-slate-100 text-left text-slate-400">
                  <th className="pb-1 pr-3">Loại phí</th>
                  <th className="pb-1 pr-3">Mô tả</th>
                  <th className="pb-1 pr-3 text-right">Gốc</th>
                  <th className="pb-1 pr-3 text-right">VAT</th>
                  <th className="pb-1 text-right">Tổng</th>
                </tr>
              </thead>
              <tbody>
                {preview.fees.map((f, i) => (
                  <tr key={i} className="border-b border-slate-50">
                    <td className="py-1 pr-3 font-medium text-slate-700">
                      {f.fee_type}
                    </td>
                    <td className="py-1 pr-3 text-slate-600">
                      {f.description}
                    </td>
                    <td className="py-1 pr-3 text-right text-slate-700">
                      {formatMoney(f.base_amount)}
                    </td>
                    <td className="py-1 pr-3 text-right text-slate-700">
                      {formatMoney(f.vat_amount)}
                    </td>
                    <td className="py-1 text-right font-bold text-slate-800">
                      {formatMoney(f.total_with_vat)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="text-[12px] font-bold">
                  <td
                    colSpan={4}
                    className="pt-2 text-right text-slate-500"
                  >
                    Tổng (bao gồm VAT):
                  </td>
                  <td className="pt-2 text-right text-rose-600">
                    {formatMoney(preview.fee_total_with_vat)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Auth doc */}
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <h3 className="font-headline text-[14px] font-bold text-slate-800">
          Nội dung uỷ quyền
        </h3>
        <div className="mt-2 max-h-[200px] overflow-y-auto rounded-xl bg-slate-50 p-3 font-mono text-[11px] leading-relaxed text-slate-700 whitespace-pre-wrap">
          {preview.auth_doc_text}
        </div>
        <p className="mt-2 text-[11px] text-slate-400">
          Hash tài liệu:{" "}
          <span className="font-mono text-slate-600">
            {preview.auth_doc_hash.slice(0, 16)}…
          </span>
        </p>
      </div>

      {/* Consent checkbox */}
      <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-white p-4">
        <input
          type="checkbox"
          checked={consentChecked}
          onChange={(e) => setConsentChecked(e.target.checked)}
          className="mt-0.5 h-4 w-4 accent-brand-indigo"
        />
        <span className="text-[13px] text-slate-700">
          Tôi đồng ý với nội dung uỷ quyền và điều khoản (version{" "}
          <span className="font-mono font-medium">
            {preview.consent_text_version}
          </span>
          )
        </span>
      </label>

      {error && (
        <div className="rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 text-[13px] text-slate-500 hover:text-brand-indigo"
        >
          <ChevronLeft className="h-4 w-4" /> Quay lại
        </button>
        <button
          type="button"
          onClick={handleSendOtp}
          disabled={!consentChecked || otpMutation.isPending}
          className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-50"
        >
          {otpMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Gửi OTP"
          )}
        </button>
      </div>
    </div>
  );
}

// ----- Step 4: Nhập OTP + ký -----

function StepSign({
  form,
  emailMasked,
  ttlMinutes,
  devCode,
  onBack,
}: {
  form: EnrollFormInput;
  emailMasked: string;
  ttlMinutes: number;
  devCode?: string | null;
  onBack: () => void;
}) {
  const signMutation = useSignEnroll();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    campaignId: number;
    approvalStatus: string;
  } | null>(null);

  async function handleSign() {
    setError(null);
    if (!otp.trim()) {
      setError("Nhập mã OTP");
      return;
    }
    try {
      const res = await signMutation.mutateAsync({
        form,
        otp_code: otp,
        consent_checked: true,
      });
      setResult({
        campaignId: res.data.campaign_id,
        approvalStatus: res.data.approval_status,
      });
    } catch (e: unknown) {
      const err = e as {
        response?: {
          data?: {
            detail?:
              | string
              | { code?: string; message?: string };
          };
        };
      };
      const detail = err.response?.data?.detail;
      if (
        typeof detail === "object" &&
        detail?.code === "REVOKE_BLOCKED_OPS_STARTED"
      ) {
        setError(detail.message ?? "Không thể thực hiện");
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Lỗi xác nhận OTP");
      }
    }
  }

  if (result) {
    const isRejected = result.approvalStatus === "rejected";
    return (
      <div className="space-y-5 text-center">
        <div
          className={
            isRejected
              ? "mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600"
              : "mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
          }
        >
          {isRejected ? (
            <AlertTriangle className="h-8 w-8" />
          ) : (
            <Check className="h-8 w-8" />
          )}
        </div>
        <h2 className="font-headline text-[22px] font-bold text-slate-800">
          {isRejected
            ? "Đăng ký đã bị từ chối tự động"
            : "Đăng ký thành công!"}
        </h2>
        <div className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm">
          <p className="text-[13px] text-slate-500">
            Trạng thái:{" "}
            <span
              className={
                isRejected
                  ? "font-bold text-red-600"
                  : "font-bold text-slate-700"
              }
            >
              {APPROVAL_STATUS_LABEL[result.approvalStatus] ??
                result.approvalStatus}
            </span>
          </p>
          {isRejected && (
            <p className="mt-2 text-[12px] text-slate-500">
              Hệ thống từ chối vì cấu hình vượt ngưỡng cho phép. Xem chi tiết
              chiến dịch để biết lý do cụ thể và điều chỉnh rồi đăng ký lại.
            </p>
          )}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
          <Link
            href={`/merchant/campaigns/${result.campaignId}`}
            className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200"
          >
            Xem chi tiết chiến dịch
          </Link>
          <Link
            href="/merchant/campaigns"
            className="rounded-xl border border-slate-200 px-5 py-2.5 text-[13px] font-medium text-slate-700 hover:bg-slate-50"
          >
            Về danh sách
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-indigo-100 bg-indigo-50 p-4 text-[13px] text-indigo-800">
        <p>
          OTP đã gửi đến{" "}
          <span className="font-bold">{emailMasked}</span>. Mã có hiệu lực
          trong{" "}
          <span className="font-bold">{ttlMinutes} phút</span>.
        </p>
        {devCode && (
          <p className="mt-1 font-mono text-[12px]">
            [Dev] Mã OTP:{" "}
            <span className="font-bold">{devCode}</span>
          </p>
        )}
      </div>

      <FieldGroup label="Nhập mã OTP">
        <input
          type="text"
          maxLength={8}
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          placeholder="- - - - - - - -"
          className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-center font-mono text-[18px] tracking-widest outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
        />
      </FieldGroup>

      {error && (
        <div className="rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 text-[13px] text-slate-500 hover:text-brand-indigo"
        >
          <ChevronLeft className="h-4 w-4" /> Quay lại
        </button>
        <button
          type="button"
          onClick={handleSign}
          disabled={signMutation.isPending}
          className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-60"
        >
          {signMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Xác nhận ký"
          )}
        </button>
      </div>
    </div>
  );
}

// ==================== Main page ====================

const STEP_LABELS = ["Chọn template", "Thông tin", "Xác nhận", "Ký số"];

export default function EnrollCampaignPage() {
  const [step, setStep] = useState(0);
  const [selectedTemplate, setSelectedTemplate] =
    useState<CampaignTemplatePublic | null>(null);
  const [formState, setFormState] = useState<FormState>({
    name: "",
    description: "",
    terms: "",
    usage_guide: "",
    support_contact: "",
    discount_value: "",
    min_order: "",
    max_discount: "",
    max_issuances: "",
    starts_at: "",
    ends_at: "",
  });
  const [enrollForm, setEnrollForm] = useState<EnrollFormInput | null>(null);
  const [preview, setPreview] = useState<CampaignEnrollPreview | null>(null);
  const [otpInfo, setOtpInfo] = useState<{
    emailMasked: string;
    ttlMinutes: number;
    devCode?: string | null;
  } | null>(null);

  function handleSelectTemplate(t: CampaignTemplatePublic) {
    setSelectedTemplate(t);
    setFormState((f) => ({
      ...f,
      terms: t.default_terms ?? "",
      usage_guide: t.default_usage_guide ?? "",
      support_contact: t.default_support_contact ?? "",
    }));
    setStep(1);
  }

  function handleFormNext(
    input: EnrollFormInput,
    previewData: CampaignEnrollPreview,
  ) {
    setEnrollForm(input);
    setPreview(previewData);
    setStep(2);
  }

  function handleOtpSent(
    emailMasked: string,
    ttlMinutes: number,
    devCode?: string | null,
  ) {
    setOtpInfo({ emailMasked, ttlMinutes, devCode });
    setStep(3);
  }

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <Link
        href="/merchant/campaigns"
        className="inline-flex items-center gap-1 text-[12px] text-slate-500 hover:text-brand-indigo"
      >
        <ChevronLeft className="h-4 w-4" /> Quay lại danh sách chiến dịch
      </Link>

      <h1 className="mt-3 font-headline text-[28px] font-bold text-slate-800">
        Đăng ký chiến dịch
      </h1>
      <p className="mt-1 text-[13px] text-slate-500">
        Đăng ký chiến dịch khuyến mãi theo chương trình managed-service.
      </p>

      {/* Stepper pills */}
      <div className="mt-6 flex items-center gap-1 overflow-x-auto pb-1">
        {STEP_LABELS.map((label, i) => {
          const done = i < step;
          const active = i === step;
          return (
            <div key={i} className="flex items-center gap-1">
              <div
                className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-medium transition-colors ${
                  done
                    ? "bg-emerald-100 text-emerald-700"
                    : active
                      ? "bg-brand-indigo text-white"
                      : "bg-slate-100 text-slate-400"
                }`}
              >
                {done ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <span className="font-bold">{i + 1}</span>
                )}
                <span>{label}</span>
              </div>
              {i < STEP_LABELS.length - 1 && (
                <div className="h-px w-4 shrink-0 bg-slate-200" />
              )}
            </div>
          );
        })}
      </div>

      {/* Step content */}
      <div className="mt-6 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm md:p-6">
        {step === 0 && (
          <StepSelectTemplate onSelect={handleSelectTemplate} />
        )}
        {step === 1 && selectedTemplate && (
          <StepFillForm
            template={selectedTemplate}
            formState={formState}
            onChange={setFormState}
            onBack={() => setStep(0)}
            onNext={handleFormNext}
          />
        )}
        {step === 2 && preview && enrollForm && (
          <StepConfirm
            preview={preview}
            form={enrollForm}
            onBack={() => setStep(1)}
            onOtpSent={handleOtpSent}
          />
        )}
        {step === 3 && enrollForm && otpInfo && (
          <StepSign
            form={enrollForm}
            emailMasked={otpInfo.emailMasked}
            ttlMinutes={otpInfo.ttlMinutes}
            devCode={otpInfo.devCode}
            onBack={() => setStep(2)}
          />
        )}
      </div>
    </main>
  );
}
