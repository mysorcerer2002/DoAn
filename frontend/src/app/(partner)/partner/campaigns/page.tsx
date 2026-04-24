"use client";

import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  Plus,
  Sparkles,
  Ticket,
  Wallet,
  X,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";


import { useCampaigns, useCreateCampaign } from "@/lib/hooks/use-partner";
import type { CampaignResponse } from "@/types/partner";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function campaignStatus(c: CampaignResponse): "running" | "upcoming" | "ended" {
  const now = Date.now();
  const start = new Date(c.starts_at).getTime();
  const end = new Date(c.ends_at).getTime();
  if (now < start) return "upcoming";
  if (now > end) return "ended";
  return "running";
}

const STATUS_CONFIG = {
  running: {
    label: "Đang chạy",
    className: "bg-emerald-500/90 text-white",
    icon: CheckCircle2,
  },
  upcoming: {
    label: "Sắp diễn ra",
    className: "bg-amber-500/90 text-white",
    icon: Clock,
  },
  ended: {
    label: "Đã kết thúc",
    className: "bg-slate-700/90 text-white",
    icon: FileText,
  },
} as const;

export default function MerchantCampaignsPage() {
  const { data: campaigns, isLoading, isError } = useCampaigns();
  const createMutation = useCreateCampaign();
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    discount_type: "percent" as "percent" | "fixed",
    discount_value: "",
    starts_at: "",
    ends_at: "",
  });
  const [error, setError] = useState<string | null>(null);

  const stats = useMemo(() => {
    if (!campaigns)
      return {
        total: 0,
        running: 0,
        upcoming: 0,
        ended: 0,
        totalIssued: 0,
        totalUsed: 0,
        totalDiscount: 0,
      };
    const result = {
      total: campaigns.length,
      running: 0,
      upcoming: 0,
      ended: 0,
      totalIssued: 0,
      totalUsed: 0,
      totalDiscount: 0,
    };
    campaigns.forEach((c) => {
      const s = campaignStatus(c);
      result[s]++;
      result.totalIssued += c.issued_count ?? 0;
      result.totalUsed += c.used_count ?? 0;
      result.totalDiscount += c.total_discount_amount ?? 0;
    });
    return result;
  }, [campaigns]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (
      !form.name.trim() ||
      !form.starts_at ||
      !form.ends_at ||
      !form.discount_value
    ) {
      setError("Vui lòng nhập đầy đủ thông tin");
      return;
    }
    try {
      await createMutation.mutateAsync({
        name: form.name.trim(),
        description: form.description.trim() || null,
        discount_type: form.discount_type,
        discount_value: Number(form.discount_value),
        starts_at: new Date(form.starts_at).toISOString(),
        ends_at: new Date(form.ends_at).toISOString(),
      });
      setModalOpen(false);
      setForm({
        name: "",
        description: "",
        discount_type: "percent",
        discount_value: "",
        starts_at: "",
        ends_at: "",
      });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? "Lỗi tạo chiến dịch");
    }
  };

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Marketing / Chiến dịch</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Chiến dịch khuyến mãi
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/partner/campaigns/enroll"
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            Đăng ký chiến dịch
          </Link>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-[13px] font-medium text-slate-700 hover:bg-slate-50 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            Tạo thủ công
          </button>
        </div>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon={Sparkles}
          label="Tổng chiến dịch"
          value={stats.total}
          tone="indigo"
        />
        <StatCard
          icon={CheckCircle2}
          label="Đang chạy"
          value={stats.running}
          tone="green"
        />
        <StatCard
          icon={Ticket}
          label="Voucher phát / dùng"
          value={`${stats.totalIssued} / ${stats.totalUsed}`}
          tone="amber"
        />
        <StatCard
          icon={Wallet}
          label="Tổng chi phí giảm giá"
          value={`${stats.totalDiscount.toLocaleString("vi-VN")}₫`}
          tone="slate"
        />
      </section>

      {isLoading ? (
        <div className="mt-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
        </div>
      ) : isError ? (
        <div className="mt-10 text-center text-red-600">
          Không tải được danh sách chiến dịch
        </div>
      ) : campaigns?.length === 0 ? (
        <div className="mt-10 rounded-2xl border border-dashed border-slate-200 bg-white p-16 text-center">
          <Sparkles className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-4 font-bold text-slate-700">Chưa có chiến dịch</p>
          <p className="mt-2 text-[13px] text-slate-500">
            Tạo chiến dịch đầu tiên để phát voucher cho khách.
          </p>
        </div>
      ) : (
        <section className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {campaigns?.map((c) => {
            const status = campaignStatus(c);
            const config = STATUS_CONFIG[status];
            const usageRate =
              c.issued_count > 0
                ? Math.round((c.used_count / c.issued_count) * 100)
                : 0;
            return (
              <Link
                key={c.id}
                href={`/partner/campaigns/${c.id}`}
                className="group overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="relative h-16 bg-gradient-to-br from-brand-indigo to-brand-violet">
                  <span
                    className={`absolute right-3 top-3 flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${config.className}`}
                  >
                    <config.icon className="h-2.5 w-2.5" />
                    {config.label}
                  </span>
                </div>
                <div className="space-y-2 p-5">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-headline text-[16px] font-bold text-slate-800 group-hover:text-brand-indigo">
                      {c.name}
                    </h3>
                    <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-1 group-hover:text-brand-indigo" />
                  </div>
                  {c.description && (
                    <p className="line-clamp-2 min-h-[2.4rem] text-[12px] text-slate-600">
                      {c.description}
                    </p>
                  )}
                  <div className="flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-1 text-[11px] font-medium text-brand-indigo w-fit">
                    <Calendar className="h-3 w-3" />
                    {formatDate(c.starts_at)} → {formatDate(c.ends_at)}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>
                      {c.discount_type === "percent"
                        ? `Giảm ${c.discount_value}%`
                        : `Giảm ${c.discount_value.toLocaleString("vi-VN")}₫`}
                    </span>
                    <span className="font-bold text-slate-700">
                      {c.issued_count}
                      {c.max_issuances ? `/${c.max_issuances}` : ""}{" "}
                      đã phát
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 border-t border-slate-100 pt-3 text-center">
                    <div>
                      <p className="text-[10px] uppercase tracking-wide text-slate-400">
                        Đã dùng
                      </p>
                      <p className="mt-0.5 text-[13px] font-bold text-emerald-600">
                        {c.used_count}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-wide text-slate-400">
                        Tỉ lệ
                      </p>
                      <p className="mt-0.5 text-[13px] font-bold text-slate-700">
                        {usageRate}%
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-wide text-slate-400">
                        Chi phí
                      </p>
                      <p className="mt-0.5 text-[13px] font-bold text-rose-600">
                        {(c.total_discount_amount / 1000).toFixed(0)}K₫
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </section>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <form
            onSubmit={handleSubmit}
            className="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-2xl"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-[20px] font-bold text-slate-800">
                Tạo chiến dịch mới
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
              <Field label="Tên chiến dịch">
                <input
                  required
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </Field>

              <Field label="Mô tả">
                <textarea
                  rows={2}
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Loại giảm giá">
                  <select
                    value={form.discount_type}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        discount_type: e.target.value as "percent" | "fixed",
                      })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
                  >
                    <option value="percent">Phần trăm (%)</option>
                    <option value="fixed">Số tiền cố định (₫)</option>
                  </select>
                </Field>
                <Field label="Giá trị giảm">
                  <input
                    required
                    type="number"
                    min="0"
                    value={form.discount_value}
                    onChange={(e) =>
                      setForm({ ...form, discount_value: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                  />
                </Field>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Bắt đầu">
                  <input
                    required
                    type="datetime-local"
                    value={form.starts_at}
                    onChange={(e) =>
                      setForm({ ...form, starts_at: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
                  />
                </Field>
                <Field label="Kết thúc">
                  <input
                    required
                    type="datetime-local"
                    value={form.ends_at}
                    onChange={(e) =>
                      setForm({ ...form, ends_at: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
                  />
                </Field>
              </div>

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
                disabled={createMutation.isPending}
                className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
              >
                {createMutation.isPending ? "Đang tạo..." : "Tạo chiến dịch"}
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-[12px] font-medium text-slate-500">{label}</label>
      {children}
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Sparkles;
  label: string;
  value: number | string;
  tone: "indigo" | "green" | "amber" | "slate";
}) {
  const toneClass =
    tone === "green"
      ? "bg-emerald-50 text-emerald-600"
      : tone === "amber"
      ? "bg-amber-50 text-amber-600"
      : tone === "slate"
      ? "bg-slate-100 text-slate-600"
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
