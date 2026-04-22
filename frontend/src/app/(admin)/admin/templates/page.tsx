"use client";

import { FileText, Plus, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  useCampaignTemplates,
  useCreateCampaignTemplate,
  useUpdateCampaignTemplate,
  useSoftDeleteCampaignTemplate,
} from "@/lib/hooks/use-admin-campaigns";
import type {
  CampaignTemplateResponse,
  CampaignTemplateCreateRequest,
} from "@/types/admin";

const SOURCE_LABELS: Record<string, string> = {
  manual: "Thủ công",
  birthday: "Sinh nhật",
  signup: "Đăng ký",
};

const PROGRAM_FORM_LABELS: Record<string, string> = {
  giam_gia: "Giảm giá",
  tang_kem: "Tặng kèm",
  may_rui_quay_so: "May rủi – quay số",
  may_rui_truc_tiep: "May rủi – trực tiếp",
  khach_hang_thuong_xuyen: "Khách hàng thường xuyên",
};

const DISCOUNT_TYPE_LABELS: Record<string, string> = {
  percent: "Phần trăm",
  fixed: "Cố định",
};

type FilterSource = "manual" | "birthday" | "signup" | "";

interface TemplateFormData {
  code: string;
  name: string;
  description: string;
  source: string;
  program_form: string;
  discount_type: string;
  max_discount_percent_cap: string;
  max_discount_value_cap: string;
  max_discount_fixed_cap: string;
  min_order_floor: string;
  max_issuances_cap: string;
  max_duration_days: string;
  min_voucher_ttl_days: string;
  max_voucher_ttl_days: string;
  is_active: boolean;
}

const EMPTY_FORM: TemplateFormData = {
  code: "",
  name: "",
  description: "",
  source: "manual",
  program_form: "giam_gia",
  discount_type: "percent",
  max_discount_percent_cap: "",
  max_discount_value_cap: "",
  max_discount_fixed_cap: "",
  min_order_floor: "0",
  max_issuances_cap: "",
  max_duration_days: "",
  min_voucher_ttl_days: "7",
  max_voucher_ttl_days: "30",
  is_active: true,
};

function templateToForm(t: CampaignTemplateResponse): TemplateFormData {
  return {
    code: t.code,
    name: t.name,
    description: t.description ?? "",
    source: t.source,
    program_form: t.program_form,
    discount_type: t.discount_type,
    max_discount_percent_cap: t.max_discount_percent_cap?.toString() ?? "",
    max_discount_value_cap: t.max_discount_value_cap?.toString() ?? "",
    max_discount_fixed_cap: t.max_discount_fixed_cap?.toString() ?? "",
    min_order_floor: t.min_order_floor.toString(),
    max_issuances_cap: t.max_issuances_cap?.toString() ?? "",
    max_duration_days: t.max_duration_days?.toString() ?? "",
    min_voucher_ttl_days: t.min_voucher_ttl_days.toString(),
    max_voucher_ttl_days: t.max_voucher_ttl_days.toString(),
    is_active: t.is_active,
  };
}

function validateForm(form: TemplateFormData): string | null {
  if (!form.code.trim() || form.code.trim().length < 3) return "Mã template tối thiểu 3 ký tự.";
  if (!form.name.trim() || form.name.trim().length < 2) return "Tên tối thiểu 2 ký tự.";
  if (form.discount_type === "percent") {
    const cap = Number(form.max_discount_percent_cap);
    const val = Number(form.max_discount_value_cap);
    if (!cap || cap < 1 || cap > 50) return "Phần trăm giảm tối đa phải từ 1–50.";
    if (!val || val < 1) return "Giá trị giảm tối đa phải > 0.";
  }
  if (form.discount_type === "fixed") {
    const cap = Number(form.max_discount_fixed_cap);
    if (!cap || cap < 1) return "Giảm cố định tối đa phải > 0.";
  }
  const minTtl = Number(form.min_voucher_ttl_days);
  const maxTtl = Number(form.max_voucher_ttl_days);
  if (maxTtl < minTtl) return "TTL tối đa phải >= TTL tối thiểu.";
  return null;
}

function buildPayload(form: TemplateFormData): CampaignTemplateCreateRequest {
  return {
    code: form.code.trim(),
    name: form.name.trim(),
    description: form.description.trim() || null,
    source: form.source,
    program_form: form.program_form,
    discount_type: form.discount_type,
    max_discount_percent_cap:
      form.discount_type === "percent" && form.max_discount_percent_cap
        ? Number(form.max_discount_percent_cap)
        : null,
    max_discount_value_cap:
      form.discount_type === "percent" && form.max_discount_value_cap
        ? Number(form.max_discount_value_cap)
        : null,
    max_discount_fixed_cap:
      form.discount_type === "fixed" && form.max_discount_fixed_cap
        ? Number(form.max_discount_fixed_cap)
        : null,
    min_order_floor: Number(form.min_order_floor) || 0,
    max_issuances_cap: form.max_issuances_cap ? Number(form.max_issuances_cap) : null,
    max_duration_days: form.max_duration_days ? Number(form.max_duration_days) : null,
    min_voucher_ttl_days: Number(form.min_voucher_ttl_days) || 7,
    max_voucher_ttl_days: Number(form.max_voucher_ttl_days) || 30,
    is_active: form.is_active,
  };
}

export default function AdminTemplatesPage() {
  const [filterSource, setFilterSource] = useState<FilterSource>("");
  const [filterActive, setFilterActive] = useState<string>("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<CampaignTemplateResponse | null>(null);
  const [form, setForm] = useState<TemplateFormData>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<CampaignTemplateResponse | null>(null);

  const filters = {
    source: filterSource || undefined,
    is_active: filterActive === "" ? undefined : filterActive === "true",
  };
  const { data: templates = [], isLoading } = useCampaignTemplates(filters);
  const createMut = useCreateCampaignTemplate();
  const updateMut = useUpdateCampaignTemplate();
  const deleteMut = useSoftDeleteCampaignTemplate();

  function openCreate() {
    setEditTarget(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setModalOpen(true);
  }

  function openEdit(t: CampaignTemplateResponse) {
    setEditTarget(t);
    setForm(templateToForm(t));
    setFormError(null);
    setModalOpen(true);
  }

  async function handleSubmit() {
    const err = validateForm(form);
    if (err) { setFormError(err); return; }
    setFormError(null);
    try {
      if (editTarget) {
        await updateMut.mutateAsync({ id: editTarget.id, data: buildPayload(form) });
      } else {
        await createMut.mutateAsync(buildPayload(form));
      }
      setModalOpen(false);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg ?? "Lỗi không xác định.");
    }
  }

  async function handleDelete(t: CampaignTemplateResponse) {
    try {
      await deleteMut.mutateAsync(t.id);
      setDeleteConfirm(null);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      window.alert(err.response?.data?.detail ?? "Không xoá được template");
    }
  }

  const f = form;
  function setField<K extends keyof TemplateFormData>(k: K, v: TemplateFormData[K]) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  const isPending = createMut.isPending || updateMut.isPending;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="h-6 w-6 text-indigo-600" />
          <h1 className="text-xl font-bold text-slate-800">Template chiến dịch</h1>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Tạo mới
        </button>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-3">
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value as FilterSource)}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        >
          <option value="">Tất cả nguồn</option>
          <option value="manual">Thủ công</option>
          <option value="birthday">Sinh nhật</option>
          <option value="signup">Đăng ký</option>
        </select>
        <select
          value={filterActive}
          onChange={(e) => setFilterActive(e.target.value)}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        >
          <option value="">Tất cả trạng thái</option>
          <option value="true">Đang hoạt động</option>
          <option value="false">Không hoạt động</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-[12px] font-semibold text-slate-500 uppercase tracking-wide">
            <tr>
              <th className="px-4 py-3 text-left">Mã</th>
              <th className="px-4 py-3 text-left">Tên</th>
              <th className="px-4 py-3 text-left">Nguồn</th>
              <th className="px-4 py-3 text-left">Hình thức</th>
              <th className="px-4 py-3 text-left">Giảm giá</th>
              <th className="px-4 py-3 text-center">Version</th>
              <th className="px-4 py-3 text-center">Trạng thái</th>
              <th className="px-4 py-3 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                  Đang tải...
                </td>
              </tr>
            )}
            {!isLoading && templates.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                  Chưa có template nào.
                </td>
              </tr>
            )}
            {templates.map((t) => (
              <tr key={t.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{t.code}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{t.name}</td>
                <td className="px-4 py-3 text-slate-600">
                  {SOURCE_LABELS[t.source] ?? t.source}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {PROGRAM_FORM_LABELS[t.program_form] ?? t.program_form}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {DISCOUNT_TYPE_LABELS[t.discount_type] ?? t.discount_type}
                </td>
                <td className="px-4 py-3 text-center text-slate-500">v{t.version}</td>
                <td className="px-4 py-3 text-center">
                  {t.is_active ? (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-700">
                      Hoạt động
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                      Tắt
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => openEdit(t)}
                      className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      title="Sửa"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    {!t.deleted_at && (
                      <button
                        type="button"
                        onClick={() => setDeleteConfirm(t)}
                        className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                        title="Xóa"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-bold text-slate-800">
              {editTarget ? "Sửa template" : "Tạo template mới"}
            </h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Mã *</label>
                  <input
                    value={f.code}
                    onChange={(e) => setField("code", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder="VD: giam20_cuoi_tuan"
                    disabled={!!editTarget}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Tên *</label>
                  <input
                    value={f.name}
                    onChange={(e) => setField("name", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder="Tên template"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">Mô tả</label>
                <textarea
                  value={f.description}
                  onChange={(e) => setField("description", e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Nguồn</label>
                  <select
                    value={f.source}
                    onChange={(e) => setField("source", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  >
                    <option value="manual">Thủ công</option>
                    <option value="birthday">Sinh nhật</option>
                    <option value="signup">Đăng ký</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Hình thức</label>
                  <select
                    value={f.program_form}
                    onChange={(e) => setField("program_form", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  >
                    {Object.entries(PROGRAM_FORM_LABELS).map(([v, l]) => (
                      <option key={v} value={v}>{l}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Loại giảm</label>
                  <select
                    value={f.discount_type}
                    onChange={(e) => setField("discount_type", e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  >
                    <option value="percent">Phần trăm</option>
                    <option value="fixed">Cố định</option>
                  </select>
                </div>
              </div>

              {f.discount_type === "percent" && (
                <div className="grid grid-cols-2 gap-4 rounded-lg bg-indigo-50 p-3">
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-slate-600">
                      Giảm tối đa (%) *
                    </label>
                    <input
                      type="number"
                      value={f.max_discount_percent_cap}
                      onChange={(e) => setField("max_discount_percent_cap", e.target.value)}
                      min={1}
                      max={50}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      placeholder="VD: 20"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-slate-600">
                      Giá trị giảm tối đa (₫) *
                    </label>
                    <input
                      type="number"
                      value={f.max_discount_value_cap}
                      onChange={(e) => setField("max_discount_value_cap", e.target.value)}
                      min={1}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      placeholder="VD: 100000"
                    />
                  </div>
                </div>
              )}

              {f.discount_type === "fixed" && (
                <div className="rounded-lg bg-amber-50 p-3">
                  <label className="mb-1 block text-xs font-semibold text-slate-600">
                    Giảm cố định tối đa (₫) *
                  </label>
                  <input
                    type="number"
                    value={f.max_discount_fixed_cap}
                    onChange={(e) => setField("max_discount_fixed_cap", e.target.value)}
                    min={1}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder="VD: 50000"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">
                    Đơn hàng tối thiểu (₫)
                  </label>
                  <input
                    type="number"
                    value={f.min_order_floor}
                    onChange={(e) => setField("min_order_floor", e.target.value)}
                    min={0}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">
                    Số lượng phát tối đa
                  </label>
                  <input
                    type="number"
                    value={f.max_issuances_cap}
                    onChange={(e) => setField("max_issuances_cap", e.target.value)}
                    min={1}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder="Để trống = không giới hạn"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">
                    Thời hạn chiến dịch tối đa (ngày)
                  </label>
                  <input
                    type="number"
                    value={f.max_duration_days}
                    onChange={(e) => setField("max_duration_days", e.target.value)}
                    min={1}
                    max={365}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder="Không giới hạn"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">
                    TTL voucher tối thiểu (ngày)
                  </label>
                  <input
                    type="number"
                    value={f.min_voucher_ttl_days}
                    onChange={(e) => setField("min_voucher_ttl_days", e.target.value)}
                    min={1}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">
                    TTL voucher tối đa (ngày)
                  </label>
                  <input
                    type="number"
                    value={f.max_voucher_ttl_days}
                    onChange={(e) => setField("max_voucher_ttl_days", e.target.value)}
                    min={1}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={f.is_active}
                  onChange={(e) => setField("is_active", e.target.checked)}
                  className="h-4 w-4 rounded"
                />
                Đang hoạt động
              </label>

              {formError && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
                  {formError}
                </p>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isPending}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {isPending ? "Đang lưu..." : editTarget ? "Lưu thay đổi" : "Tạo mới"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirm modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-2 text-base font-bold text-slate-800">Xác nhận xóa template</h2>
            <p className="mb-4 text-sm text-slate-600">
              Xóa template <strong>{deleteConfirm.name}</strong>? Thao tác này là soft delete — template vẫn tham chiếu được từ các campaign cũ.
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setDeleteConfirm(null)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={() => handleDelete(deleteConfirm)}
                disabled={deleteMut.isPending}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMut.isPending ? "Đang xóa..." : "Xóa"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
