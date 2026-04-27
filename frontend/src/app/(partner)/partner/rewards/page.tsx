"use client";

import {
  CheckCircle2,
  Clock,
  Eye,
  Gift,
  Loader2,
  Pencil,
  Plus,
  Send,
  Ticket,
  Trash2,
  TrendingUp,
  Wallet,
  X,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  useCreateReward,
  useDeleteReward,
  useRewardStats,
  useRewards,
  useUpdateReward,
} from "@/lib/hooks/use-partner";
import type {
  RewardCreateRequest,
  RewardOfferType,
  RewardResponse,
  RewardUpdateRequest,
} from "@/types/partner";

// ─── Form state ──────────────────────────────────────────────────────────────

type FormState = {
  name: string;
  description: string;
  points_cost: string;
  stock: string;
  is_active: boolean;
  offer_type: RewardOfferType;
  offer_value: string;
  offer_label: string;
  min_purchase_enabled: boolean;
  min_purchase_amount: string;
  valid_until: string;
  terms: string;
};

const defaultForm: FormState = {
  name: "",
  description: "",
  points_cost: "100",
  stock: "",
  is_active: true,
  offer_type: "PERCENT_DISCOUNT",
  offer_value: "10",
  offer_label: "Giảm 10%",
  min_purchase_enabled: false,
  min_purchase_amount: "",
  valid_until: "",
  terms: "",
};

function fromReward(r: RewardResponse): FormState {
  return {
    name: r.name,
    description: r.description ?? "",
    points_cost: String(r.points_cost),
    stock: r.stock != null ? String(r.stock) : "",
    is_active: r.is_active,
    offer_type: r.offer_type,
    offer_value: r.offer_value != null ? String(r.offer_value) : "",
    offer_label: r.offer_label,
    min_purchase_enabled: r.min_purchase_amount != null,
    min_purchase_amount:
      r.min_purchase_amount != null ? String(r.min_purchase_amount) : "",
    valid_until: r.valid_until ?? "",
    terms: r.terms ?? "",
  };
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function MerchantRewardsPage() {
  const { data: rewards, isLoading, isError } = useRewards({ limit: 200 });
  const createMutation = useCreateReward();
  const updateMutation = useUpdateReward();
  const deleteMutation = useDeleteReward();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingReward, setEditingReward] = useState<RewardResponse | null>(
    null
  );
  const [form, setForm] = useState<FormState>(defaultForm);
  const [statsRewardId, setStatsRewardId] = useState<number | null>(null);
  const statsReward = rewards?.find((r) => r.id === statsRewardId) ?? null;

  const stats = {
    total: rewards?.length ?? 0,
    active: rewards?.filter((r) => r.is_active && !r.deleted_at).length ?? 0,
    outOfStock: rewards?.filter((r) => r.stock === 0).length ?? 0,
  };

  const openCreateModal = () => {
    setEditingReward(null);
    setForm(defaultForm);
    setModalOpen(true);
  };

  const openEditModal = (reward: RewardResponse) => {
    setEditingReward(reward);
    setForm(fromReward(reward));
    setModalOpen(true);
  };

  const handleSubmit = async (
    formValues: FormState,
    isEdit: boolean
  ): Promise<string | null> => {
    const offer_value_num =
      formValues.offer_value.trim() !== ""
        ? Number(formValues.offer_value)
        : null;
    const min_purchase_num =
      formValues.min_purchase_enabled &&
      formValues.min_purchase_amount.trim() !== ""
        ? Number(formValues.min_purchase_amount)
        : null;

    if (isEdit && editingReward) {
      const data: RewardUpdateRequest = {
        name: formValues.name.trim() || undefined,
        description: formValues.description.trim() || null,
        points_cost: Number(formValues.points_cost),
        stock:
          formValues.stock.trim() === "" ? null : Number(formValues.stock),
        is_active: formValues.is_active,
        offer_value:
          editingReward.offer_type === "ITEM_GIFT" ? null : offer_value_num,
        offer_label: formValues.offer_label.trim(),
        min_purchase_amount:
          editingReward.offer_type === "ITEM_GIFT" ? null : min_purchase_num,
        valid_until: formValues.valid_until || null,
        terms: formValues.terms.trim() || null,
      };
      await updateMutation.mutateAsync({ id: editingReward.id, data });
    } else {
      const data: RewardCreateRequest = {
        name: formValues.name.trim(),
        description: formValues.description.trim() || null,
        points_cost: Number(formValues.points_cost),
        stock:
          formValues.stock.trim() === "" ? null : Number(formValues.stock),
        is_active: formValues.is_active,
        offer_type: formValues.offer_type,
        offer_value:
          formValues.offer_type === "ITEM_GIFT" ? null : offer_value_num,
        offer_label: formValues.offer_label.trim(),
        min_purchase_amount:
          formValues.offer_type === "ITEM_GIFT" ? null : min_purchase_num,
        valid_until: formValues.valid_until || null,
        terms: formValues.terms.trim() || null,
      };
      await createMutation.mutateAsync(data);
    }
    return null;
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Xác nhận xoá reward này?")) return;
    try {
      await deleteMutation.mutateAsync(id);
    } catch {
      /* ignore */
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Phần thưởng / Quản lý</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Quản lý quà tặng
          </h1>
        </div>
        <button
          type="button"
          onClick={openCreateModal}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          Thêm quà mới
        </button>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon={Gift}
          label="Tổng quà"
          value={stats.total.toString()}
          tone="indigo"
        />
        <StatCard
          icon={CheckCircle2}
          label="Đang bán"
          value={stats.active.toString()}
          tone="green"
        />
        <StatCard
          icon={XCircle}
          label="Hết hàng"
          value={stats.outOfStock.toString()}
          tone="amber"
        />
        <StatCard
          icon={TrendingUp}
          label="Tất cả lần đổi"
          value="—"
          tone="orange"
        />
      </section>

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="p-6 text-center text-red-600">
            Không tải được quà tặng
          </div>
        ) : rewards?.length === 0 ? (
          <div className="p-16 text-center">
            <Gift className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">Chưa có quà tặng</p>
            <p className="mt-2 text-[13px] text-slate-500">
              Thêm phần thưởng đầu tiên để khách đổi điểm.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="border-b border-slate-100 bg-slate-50">
                <tr className="text-left text-[11px] font-bold uppercase text-slate-500">
                  <th className="px-4 py-3">Quà</th>
                  <th className="px-4 py-3 text-right">Điểm</th>
                  <th className="px-4 py-3 text-right">Tồn kho</th>
                  <th className="px-4 py-3 text-center">Trạng thái</th>
                  <th className="px-4 py-3 text-right">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {rewards?.map((reward) => (
                  <tr
                    key={reward.id}
                    className="border-b border-slate-50 last:border-b-0 hover:bg-slate-50/50"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-[13px] font-bold text-slate-800">
                            {reward.name}
                          </p>
                          <OfferTypeChip reward={reward} />
                        </div>
                        {reward.description && (
                          <p className="text-[11px] text-slate-400">
                            {reward.description}
                          </p>
                        )}
                        {reward.min_purchase_amount != null && (
                          <p className="text-[11px] text-slate-400">
                            Đơn từ{" "}
                            {reward.min_purchase_amount.toLocaleString("vi-VN")}
                            đ
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-headline text-[14px] font-bold text-brand-orange">
                      {reward.points_cost.toLocaleString("vi-VN")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {reward.stock === null ? (
                        <span className="text-[12px] text-slate-500">
                          Không giới hạn
                        </span>
                      ) : reward.stock === 0 ? (
                        <span className="text-[12px] font-bold text-red-500">
                          Hết hàng
                        </span>
                      ) : (
                        <span className="text-[12px] font-bold text-slate-700">
                          {reward.stock}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {reward.deleted_at ? (
                        <span className="rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-bold text-red-600">
                          Đã xoá
                        </span>
                      ) : reward.is_active ? (
                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-bold text-emerald-600">
                          Đang bán
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-600">
                          Tạm dừng
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => setStatsRewardId(reward.id)}
                          aria-label="Xem chi tiết"
                          className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => openEditModal(reward)}
                          aria-label="Sửa"
                          className="flex h-8 w-8 items-center justify-center rounded-lg text-brand-indigo hover:bg-indigo-50"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(reward.id)}
                          aria-label="Xoá"
                          className="flex h-8 w-8 items-center justify-center rounded-lg text-red-500 hover:bg-red-50"
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {modalOpen && (
        <RewardFormModal
          editingReward={editingReward}
          initialForm={form}
          isPending={isPending}
          onClose={() => setModalOpen(false)}
          onSubmit={handleSubmit}
        />
      )}

      {statsRewardId != null && (
        <RewardStatsModal
          rewardId={statsRewardId}
          rewardName={statsReward?.name ?? ""}
          onClose={() => setStatsRewardId(null)}
        />
      )}
    </main>
  );
}

// ─── Offer type chip ──────────────────────────────────────────────────────────

function OfferTypeChip({ reward }: { reward: RewardResponse }) {
  const cls =
    reward.offer_type === "ITEM_GIFT"
      ? "bg-orange-100 text-orange-700"
      : "bg-indigo-100 text-indigo-700";
  return (
    <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${cls}`}>
      {reward.offer_label}
    </span>
  );
}

// ─── Auto-suggest helper ──────────────────────────────────────────────────────

function suggestLabel(
  offerType: RewardOfferType,
  offerValueStr: string
): string {
  const val = Number(offerValueStr);
  if (offerType === "PERCENT_DISCOUNT" && val > 0) {
    return `Giảm ${val}%`;
  }
  if (offerType === "FIXED_DISCOUNT" && val > 0) {
    return `Giảm ${val.toLocaleString("vi-VN")}đ`;
  }
  if (offerType === "ITEM_GIFT") {
    return "Quà tặng";
  }
  return "";
}

// ─── Form modal ───────────────────────────────────────────────────────────────

function RewardFormModal({
  editingReward,
  initialForm,
  isPending,
  onClose,
  onSubmit,
}: {
  editingReward: RewardResponse | null;
  initialForm: FormState;
  isPending: boolean;
  onClose: () => void;
  onSubmit: (
    form: FormState,
    isEdit: boolean
  ) => Promise<string | null>;
}) {
  const isEdit = editingReward != null;
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState<string | null>(null);
  // Track whether user has manually edited offer_label (suppress auto-suggest)
  const [userEditedLabel, setUserEditedLabel] = useState(false);

  // Auto-suggest offer_label when offer_type or offer_value changes
  useEffect(() => {
    if (userEditedLabel) return;
    const suggested = suggestLabel(form.offer_type, form.offer_value);
    if (suggested) {
      setForm((prev) => ({ ...prev, offer_label: suggested }));
    }
  }, [form.offer_type, form.offer_value, userEditedLabel]);

  const setField = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleTypeChange = (newType: RewardOfferType) => {
    if (isEdit) return; // offer_type immutable in edit mode
    setForm((prev) => ({
      ...prev,
      offer_type: newType,
      offer_value: newType === "ITEM_GIFT" ? "" : "10",
      min_purchase_enabled: false,
      min_purchase_amount: "",
    }));
    setUserEditedLabel(false); // re-enable auto-suggest on type change
  };

  // Validate FE-side before submit
  const validate = (): string | null => {
    if (!form.name.trim()) return "Tên quà bắt buộc";
    const pts = Number(form.points_cost);
    if (!form.points_cost || Number.isNaN(pts) || pts <= 0)
      return "Điểm cần phải lớn hơn 0";
    if (!form.offer_label.trim()) return "Nhãn ngắn bắt buộc";
    if (form.offer_label.trim().length > 120)
      return "Nhãn ngắn tối đa 120 ký tự";

    const effectiveType = isEdit ? editingReward!.offer_type : form.offer_type;
    if (effectiveType === "PERCENT_DISCOUNT") {
      const v = Number(form.offer_value);
      if (!form.offer_value || Number.isNaN(v) || v < 1 || v > 100)
        return "Phần trăm giảm phải từ 1 đến 100";
    } else if (effectiveType === "FIXED_DISCOUNT") {
      const v = Number(form.offer_value);
      if (!form.offer_value || Number.isNaN(v) || v <= 0)
        return "Số tiền giảm phải lớn hơn 0";
    }

    if (
      form.min_purchase_enabled &&
      effectiveType !== "ITEM_GIFT"
    ) {
      const mp = Number(form.min_purchase_amount);
      if (!form.min_purchase_amount || Number.isNaN(mp) || mp <= 0)
        return "Hoá đơn tối thiểu phải lớn hơn 0";
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const validationErr = validate();
    if (validationErr) {
      setError(validationErr);
      return;
    }
    try {
      await onSubmit(form, isEdit);
      onClose();
    } catch (err: unknown) {
      // Map BE 422 detail (string or array) to user-facing message
      let msg = "Lỗi xảy ra";
      if (err && typeof err === "object" && "response" in err) {
        const resp = (err as { response?: { data?: { detail?: unknown } } })
          .response;
        const detail = resp?.data?.detail;
        if (typeof detail === "string") {
          msg = detail;
        } else if (Array.isArray(detail) && detail.length > 0) {
          const first = detail[0];
          msg =
            typeof first?.msg === "string"
              ? first.msg
              : JSON.stringify(first);
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    }
  };

  // Current effective offer_type (immutable in edit: always show editingReward's type)
  const effectiveType = isEdit ? editingReward!.offer_type : form.offer_type;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md max-h-[90vh] overflow-y-auto space-y-4 rounded-2xl bg-white p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-[20px] font-bold text-slate-800">
            {isEdit ? "Sửa quà tặng" : "Thêm quà tặng"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
            aria-label="Đóng"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Loại quà */}
        <div>
          <label
            htmlFor="offer_type"
            className="text-[12px] font-medium text-slate-500"
          >
            Loại quà <span className="text-rose-500">*</span>
          </label>
          <select
            id="offer_type"
            value={effectiveType}
            onChange={(e) =>
              handleTypeChange(e.target.value as RewardOfferType)
            }
            disabled={isEdit}
            aria-disabled={isEdit}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <option value="PERCENT_DISCOUNT">Voucher giảm phần trăm</option>
            <option value="FIXED_DISCOUNT">Voucher giảm số tiền</option>
            <option value="ITEM_GIFT">Quà tặng hiện vật</option>
          </select>
          {isEdit && (
            <p className="mt-1 text-[11px] text-slate-400">
              Loại quà không thể đổi sau khi tạo. Cần đổi → tạo quà mới.
            </p>
          )}
        </div>

        {/* Tên quà */}
        <div>
          <label
            htmlFor="reward_name"
            className="text-[12px] font-medium text-slate-500"
          >
            Tên quà <span className="text-rose-500">*</span>
          </label>
          <input
            id="reward_name"
            required
            type="text"
            maxLength={255}
            value={form.name}
            onChange={(e) => setField("name", e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>

        {/* Mô tả */}
        <div>
          <label
            htmlFor="reward_desc"
            className="text-[12px] font-medium text-slate-500"
          >
            Mô tả
          </label>
          <textarea
            id="reward_desc"
            rows={2}
            value={form.description}
            onChange={(e) => setField("description", e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>

        {/* offer_value — PERCENT */}
        {effectiveType === "PERCENT_DISCOUNT" && (
          <div>
            <label
              htmlFor="offer_value_pct"
              className="text-[12px] font-medium text-slate-500"
            >
              % giảm (1–100) <span className="text-rose-500">*</span>
            </label>
            <div className="relative mt-1">
              <input
                id="offer_value_pct"
                type="number"
                min={1}
                max={100}
                value={form.offer_value}
                onChange={(e) => setField("offer_value", e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 pr-8 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[12px] text-slate-400">
                %
              </span>
            </div>
          </div>
        )}

        {/* offer_value — FIXED */}
        {effectiveType === "FIXED_DISCOUNT" && (
          <div>
            <label
              htmlFor="offer_value_fixed"
              className="text-[12px] font-medium text-slate-500"
            >
              Số tiền giảm <span className="text-rose-500">*</span>
            </label>
            <div className="relative mt-1">
              <input
                id="offer_value_fixed"
                type="number"
                min={1}
                value={form.offer_value}
                onChange={(e) => setField("offer_value", e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 pr-6 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[12px] text-slate-400">
                đ
              </span>
            </div>
          </div>
        )}

        {/* Nhãn ngắn (offer_label) */}
        <div>
          <label
            htmlFor="offer_label"
            className="text-[12px] font-medium text-slate-500"
          >
            Nhãn ngắn <span className="text-rose-500">*</span>
          </label>
          <input
            id="offer_label"
            type="text"
            maxLength={120}
            value={form.offer_label}
            onChange={(e) => {
              setUserEditedLabel(true);
              setField("offer_label", e.target.value);
            }}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
          <p className="mt-1 text-[11px] text-slate-400">
            Hiển thị trên thẻ quà, vd "Giảm 20%", "1 ly cafe".
          </p>
        </div>

        {/* min_purchase toggle — chỉ PERCENT + FIXED */}
        {effectiveType !== "ITEM_GIFT" && (
          <div>
            <label className="flex items-center gap-2 text-[13px] text-slate-700">
              <input
                type="checkbox"
                id="min_purchase_toggle"
                checked={form.min_purchase_enabled}
                onChange={(e) => {
                  setField("min_purchase_enabled", e.target.checked);
                  if (!e.target.checked) setField("min_purchase_amount", "");
                }}
                className="h-4 w-4 rounded border-slate-300 text-brand-indigo"
              />
              Yêu cầu hoá đơn tối thiểu
            </label>
            {form.min_purchase_enabled && (
              <div className="relative mt-2">
                <input
                  id="min_purchase_amount"
                  type="number"
                  min={1}
                  aria-label="Hoá đơn tối thiểu"
                  placeholder="Nhập số tiền tối thiểu"
                  value={form.min_purchase_amount}
                  onChange={(e) =>
                    setField("min_purchase_amount", e.target.value)
                  }
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 pr-6 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[12px] text-slate-400">
                  đ
                </span>
              </div>
            )}
          </div>
        )}

        {/* Điểm + tồn kho */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label
              htmlFor="points_cost"
              className="text-[12px] font-medium text-slate-500"
            >
              Điểm cần <span className="text-rose-500">*</span>
            </label>
            <input
              id="points_cost"
              required
              type="number"
              min={1}
              value={form.points_cost}
              onChange={(e) => setField("points_cost", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
            />
          </div>
          <div>
            <label
              htmlFor="stock"
              className="text-[12px] font-medium text-slate-500"
            >
              Tồn kho (trống = vô hạn)
            </label>
            <input
              id="stock"
              type="number"
              min={0}
              value={form.stock}
              onChange={(e) => setField("stock", e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
            />
          </div>
        </div>

        {/* Hạn dùng */}
        <div>
          <label
            htmlFor="valid_until"
            className="text-[12px] font-medium text-slate-500"
          >
            Hạn dùng
          </label>
          <input
            id="valid_until"
            type="date"
            value={form.valid_until}
            onChange={(e) => setField("valid_until", e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>

        {/* Điều khoản */}
        <div>
          <label
            htmlFor="terms"
            className="text-[12px] font-medium text-slate-500"
          >
            Điều khoản
          </label>
          <textarea
            id="terms"
            rows={3}
            placeholder="Điều khoản áp dụng..."
            value={form.terms}
            onChange={(e) => setField("terms", e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>

        {/* Đang bán */}
        <label className="flex items-center gap-2 text-[13px] text-slate-700">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setField("is_active", e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-brand-indigo"
          />
          Đang bán
        </label>

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">
            {error}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2 text-[13px] font-medium text-slate-700 hover:bg-slate-50"
          >
            Huỷ
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
          >
            {isPending ? "Đang lưu..." : isEdit ? "Cập nhật" : "Thêm mới"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─── Stats modal ──────────────────────────────────────────────────────────────

function RewardStatsModal({
  rewardId,
  rewardName,
  onClose,
}: {
  rewardId: number;
  rewardName: string;
  onClose: () => void;
}) {
  const { data, isLoading, isError } = useRewardStats(rewardId);

  const offerLabel =
    data?.offer_type === "PERCENT_DISCOUNT"
      ? "Voucher % giảm giá"
      : data?.offer_type === "FIXED_DISCOUNT"
      ? "Voucher giảm tiền"
      : "Quà tặng";
  const offerBadgeTone =
    data?.offer_type === "ITEM_GIFT"
      ? "bg-indigo-50 text-brand-indigo"
      : "bg-orange-50 text-brand-orange";
  const usageRate =
    data && data.issued > 0
      ? Math.round((data.used / data.issued) * 100)
      : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative bg-gradient-to-br from-brand-indigo to-indigo-600 px-6 pb-5 pt-6 text-white">
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-white/15 text-white hover:bg-white/25"
            aria-label="Đóng"
          >
            <X className="h-4 w-4" />
          </button>
          <p className="text-[11px] uppercase tracking-wider text-white/70">
            Chi tiết quà tặng
          </p>
          <h2 className="mt-1 font-headline text-[20px] font-bold leading-tight">
            {rewardName}
          </h2>
          {data && (
            <span
              className={`mt-3 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${offerBadgeTone}`}
            >
              <Gift className="h-3 w-3" />
              {offerLabel}
            </span>
          )}
        </div>

        <div className="space-y-4 p-6">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-brand-indigo" />
            </div>
          ) : isError || !data ? (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">
              Không tải được thống kê.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                <StatTile
                  icon={Send}
                  label="Đã phát hành"
                  value={data.issued.toLocaleString("vi-VN")}
                  tone="indigo"
                />
                <StatTile
                  icon={Clock}
                  label="Đã đổi (chưa dùng)"
                  value={data.redeemed.toLocaleString("vi-VN")}
                  tone="amber"
                />
                <StatTile
                  icon={CheckCircle2}
                  label="Đã dùng"
                  value={data.used.toLocaleString("vi-VN")}
                  tone="green"
                />
                <StatTile
                  icon={XCircle}
                  label="Đã hết hạn"
                  value={data.expired.toLocaleString("vi-VN")}
                  tone="slate"
                />
              </div>

              {data.issued > 0 && (
                <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                  <div className="flex items-center justify-between text-[12px] text-slate-600">
                    <span>Tỷ lệ sử dụng</span>
                    <span className="font-semibold text-slate-800">
                      {usageRate}%
                    </span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{ width: `${usageRate}%` }}
                    />
                  </div>
                </div>
              )}

              {data.total_discount_cost != null ? (
                <div className="rounded-xl border border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50 p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-orange-100 text-brand-orange">
                      <Wallet className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <p className="text-[11px] font-medium text-orange-700/80">
                        Tổng chi phí giảm giá
                      </p>
                      <p className="font-headline text-[22px] font-bold text-brand-orange">
                        {data.total_discount_cost.toLocaleString("vi-VN")}đ
                      </p>
                    </div>
                  </div>
                  <p className="mt-2 text-[11px] text-slate-500">
                    Tổng tiền đã giảm cho khách qua {data.used} lượt dùng.
                  </p>
                </div>
              ) : (
                <div className="flex items-start gap-2.5 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                  <Ticket className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                  <p className="text-[12px] text-slate-500">
                    <span className="font-semibold text-slate-600">
                      Loại quà tặng
                    </span>{" "}
                    — không phát sinh chi phí giảm giá. Chỉ áp dụng với
                    voucher giảm % hoặc giảm tiền cố định.
                  </p>
                </div>
              )}
            </>
          )}

          <div className="flex justify-end pt-1">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-200 px-4 py-2 text-[13px] font-medium text-slate-700 hover:bg-slate-50"
            >
              Đóng
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Utility components ───────────────────────────────────────────────────────

function StatTile({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Gift;
  label: string;
  value: string;
  tone: "indigo" | "amber" | "green" | "slate";
}) {
  const toneClass =
    tone === "green"
      ? "bg-emerald-50 text-emerald-600"
      : tone === "amber"
      ? "bg-amber-50 text-amber-600"
      : tone === "slate"
      ? "bg-slate-100 text-slate-500"
      : "bg-indigo-50 text-brand-indigo";
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3">
      <div className="flex items-center gap-2">
        <div
          className={`flex h-7 w-7 items-center justify-center rounded-lg ${toneClass}`}
        >
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-[11px] text-slate-500">{label}</p>
      </div>
      <p className="mt-1.5 font-headline text-[20px] font-bold text-slate-800">
        {value}
      </p>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Gift;
  label: string;
  value: string;
  tone: "indigo" | "green" | "amber" | "orange";
}) {
  const toneClass =
    tone === "green"
      ? "bg-emerald-50 text-emerald-600"
      : tone === "amber"
      ? "bg-amber-50 text-amber-600"
      : tone === "orange"
      ? "bg-orange-50 text-brand-orange"
      : "bg-indigo-50 text-brand-indigo";
  return (
    <article className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-xl ${toneClass}`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-[11px] text-slate-400">{label}</p>
        <p className="font-headline text-[22px] font-bold text-slate-800">
          {value}
        </p>
      </div>
    </article>
  );
}
