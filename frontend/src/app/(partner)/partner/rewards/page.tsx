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
import { useState } from "react";

import {
  useCreateReward,
  useDeleteReward,
  useRewardStats,
  useRewards,
  useUpdateReward,
} from "@/lib/hooks/use-partner";
import type { RewardResponse } from "@/types/partner";

type FormState = {
  id: number | null;
  name: string;
  description: string;
  points_cost: string;
  stock: string;
  is_active: boolean;
};

const emptyForm: FormState = {
  id: null,
  name: "",
  description: "",
  points_cost: "",
  stock: "",
  is_active: true,
};

export default function MerchantRewardsPage() {
  const { data: rewards, isLoading, isError } = useRewards({ limit: 200 });
  const createMutation = useCreateReward();
  const updateMutation = useUpdateReward();
  const deleteMutation = useDeleteReward();

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [statsRewardId, setStatsRewardId] = useState<number | null>(null);
  const statsReward = rewards?.find((r) => r.id === statsRewardId) ?? null;

  const stats = {
    total: rewards?.length ?? 0,
    active: rewards?.filter((r) => r.is_active && !r.deleted_at).length ?? 0,
    outOfStock: rewards?.filter((r) => r.stock === 0).length ?? 0,
  };

  const openCreateModal = () => {
    setForm(emptyForm);
    setError(null);
    setModalOpen(true);
  };

  const openEditModal = (reward: RewardResponse) => {
    setForm({
      id: reward.id,
      name: reward.name,
      description: reward.description ?? "",
      points_cost: String(reward.points_cost),
      stock: reward.stock != null ? String(reward.stock) : "",
      is_active: reward.is_active,
    });
    setError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      points_cost: Number(form.points_cost),
      stock: form.stock.trim() === "" ? null : Number(form.stock),
      is_active: form.is_active,
    };
    if (!payload.name || Number.isNaN(payload.points_cost)) {
      setError("Vui lòng nhập đầy đủ tên và điểm");
      return;
    }
    try {
      if (form.id != null) {
        await updateMutation.mutateAsync({ id: form.id, data: payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setModalOpen(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Lỗi xảy ra";
      setError(msg);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Xác nhận xoá reward này?")) return;
    try {
      await deleteMutation.mutateAsync(id);
    } catch {
      /* ignore */
    }
  };

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
                      <p className="text-[13px] font-bold text-slate-800">
                        {reward.name}
                      </p>
                      {reward.description && (
                        <p className="text-[11px] text-slate-400">
                          {reward.description}
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <form
            onSubmit={handleSubmit}
            className="w-full max-w-md space-y-4 rounded-2xl bg-white p-6 shadow-2xl"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-[20px] font-bold text-slate-800">
                {form.id != null ? "Sửa quà tặng" : "Thêm quà tặng"}
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
                aria-label="Đóng"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[12px] font-medium text-slate-500">
                  Tên quà
                </label>
                <input
                  required
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>

              <div>
                <label className="text-[12px] font-medium text-slate-500">
                  Mô tả
                </label>
                <textarea
                  rows={2}
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[12px] font-medium text-slate-500">
                    Điểm cần
                  </label>
                  <input
                    required
                    type="number"
                    min="0"
                    value={form.points_cost}
                    onChange={(e) =>
                      setForm({ ...form, points_cost: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                  />
                </div>
                <div>
                  <label className="text-[12px] font-medium text-slate-500">
                    Tồn kho (trống = vô hạn)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={form.stock}
                    onChange={(e) =>
                      setForm({ ...form, stock: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                  />
                </div>
              </div>

              <label className="flex items-center gap-2 text-[13px] text-slate-700">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) =>
                    setForm({ ...form, is_active: e.target.checked })
                  }
                  className="h-4 w-4 rounded border-slate-300 text-brand-indigo"
                />
                Đang bán
              </label>

              {error && (
                <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">
                  {error}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-xl border border-slate-200 px-4 py-2 text-[13px] font-medium text-slate-700 hover:bg-slate-50"
              >
                Huỷ
              </button>
              <button
                type="submit"
                disabled={
                  createMutation.isPending || updateMutation.isPending
                }
                className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
              >
                {createMutation.isPending || updateMutation.isPending
                  ? "Đang lưu..."
                  : form.id != null
                  ? "Cập nhật"
                  : "Thêm mới"}
              </button>
            </div>
          </form>
        </div>
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
  const usageRate = data && data.issued > 0 ? Math.round((data.used / data.issued) * 100) : 0;

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
          <p className="text-[11px] uppercase tracking-wider text-white/70">Chi tiết quà tặng</p>
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
                    <span className="font-semibold text-slate-800">{usageRate}%</span>
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
                    <span className="font-semibold text-slate-600">Loại quà tặng</span> —
                    không phát sinh chi phí giảm giá. Chỉ áp dụng với voucher giảm % hoặc
                    giảm tiền cố định.
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
        <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${toneClass}`}>
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-[11px] text-slate-500">{label}</p>
      </div>
      <p className="mt-1.5 font-headline text-[20px] font-bold text-slate-800">{value}</p>
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
