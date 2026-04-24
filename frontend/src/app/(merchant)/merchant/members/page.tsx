"use client";

import {
  Ban,
  Coins,
  Crown,
  Download,
  Eye,
  Loader2,
  Pencil,
  Plus,
  Search,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";

import { useMembers } from "@/lib/hooks/use-partner";
import type { MemberResponse } from "@/types/partner";

function formatVnd(n: number): string {
  return n.toLocaleString("vi-VN") + " ₫";
}

function formatRelative(iso: string | null): string {
  if (!iso) return "Chưa có";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

function getInitials(name: string | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(-2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

function tierGradient(tier: string | null): string {
  if (!tier) return "from-slate-400 to-slate-300";
  const map: Record<string, string> = {
    "Hạng Đồng": "from-amber-700 to-amber-500",
    "Hạng Bạc": "from-slate-400 to-slate-300",
    "Hạng Vàng": "from-amber-500 to-orange-400",
    "Hạng Bạch Kim": "from-violet-500 to-brand-indigo",
  };
  return map[tier] ?? "from-slate-400 to-slate-300";
}

export default function MerchantMembersPage() {
  const [search, setSearch] = useState("");
  const { data: members, isLoading, isError } = useMembers({ limit: 100 });

  const filtered = useMemo(() => {
    if (!members) return [];
    if (!search) return members;
    const q = search.toLowerCase();
    return members.filter(
      (m) =>
        m.user_full_name?.toLowerCase().includes(q) ||
        m.user_phone?.toLowerCase().includes(q) ||
        m.user_email?.toLowerCase().includes(q)
    );
  }, [members, search]);

  const total = members?.length ?? 0;
  const active30d = members
    ? members.filter(
        (m) =>
          m.last_activity_at &&
          Date.now() - new Date(m.last_activity_at).getTime() <
            30 * 24 * 60 * 60 * 1000
      ).length
    : 0;
  const totalPoints = members
    ? members.reduce((s, m) => s + m.points_balance, 0)
    : 0;

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <h1 className="font-headline text-[32px] font-bold text-slate-800">
            Danh sách thành viên
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Quản lý {total} thành viên
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl border border-brand-indigo bg-white px-4 py-2.5 text-[13px] font-bold text-brand-indigo hover:bg-brand-indigo/5"
          >
            <Download className="h-4 w-4" />
            Xuất Excel
          </button>
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-4 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            Thêm thành viên
          </button>
        </div>
      </header>

      {/* KPI strip */}
      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon={Users}
          label="Tổng thành viên"
          value={total.toLocaleString("vi-VN")}
          tone="indigo"
        />
        <StatCard
          icon={Users}
          label="Hoạt động 30 ngày"
          value={active30d.toLocaleString("vi-VN")}
          tone="green"
        />
        <StatCard
          icon={Coins}
          label="Tổng điểm hiện có"
          value={totalPoints.toLocaleString("vi-VN")}
          tone="orange"
        />
        <StatCard
          icon={Crown}
          label="Hoạt động / Tổng"
          value={total > 0 ? `${Math.round((active30d / total) * 100)}%` : "0%"}
          tone="indigo"
        />
      </section>

      <section className="mt-5 rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo tên, SĐT, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>
      </section>

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="p-6 text-center text-red-600">
            Không tải được danh sách thành viên
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center">
            <Users className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              {search ? "Không tìm thấy thành viên" : "Chưa có thành viên"}
            </p>
            <p className="mt-2 text-[13px] text-slate-500">
              {search
                ? "Thử tìm với từ khoá khác"
                : "Khách sẽ xuất hiện sau khi tích điểm lần đầu"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr className="text-left text-[11px] font-bold uppercase text-slate-500">
                <th scope="col" className="px-4 py-3">#</th>
                <th scope="col" className="px-4 py-3">Khách hàng</th>
                <th scope="col" className="px-4 py-3">Liên hệ</th>
                <th scope="col" className="px-4 py-3 text-center">Hạng</th>
                <th scope="col" className="px-4 py-3 text-right">Điểm</th>
                <th scope="col" className="px-4 py-3 text-right">Tích lũy</th>
                <th scope="col" className="px-4 py-3 text-right">Lần cuối GD</th>
                <th scope="col" className="px-4 py-3 text-right">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m: MemberResponse, idx) => (
                <tr
                  key={m.membership_id}
                  className="border-b border-slate-50 last:border-b-0 hover:bg-slate-50/50"
                >
                  <td className="px-4 py-3 text-[12px] text-slate-400">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-200 to-violet-200 text-[12px] font-bold text-indigo-700">
                        {getInitials(m.user_full_name)}
                      </div>
                      <div>
                        <p className="text-[13px] font-bold text-slate-800">
                          {m.user_full_name ?? "Chưa đặt tên"}
                        </p>
                        <p className="text-[10px] font-mono text-slate-400">
                          M-{m.membership_id}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-[12px] font-medium text-slate-700">
                      {m.user_phone ?? "—"}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {m.user_email ?? "—"}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center">
                      {m.current_tier_name ? (
                        <span
                          className={`flex items-center gap-1 rounded-full bg-gradient-to-r ${tierGradient(
                            m.current_tier_name
                          )} px-2 py-0.5 text-[11px] font-bold text-white`}
                        >
                          <Crown className="h-2.5 w-2.5" fill="white" />
                          {m.current_tier_name}
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">
                          Chưa phân
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-headline text-[14px] font-bold text-brand-orange">
                    {m.points_balance.toLocaleString("vi-VN")}
                  </td>
                  <td className="px-4 py-3 text-right text-[12px] text-slate-600">
                    {m.total_points_earned.toLocaleString("vi-VN")}
                  </td>
                  <td className="px-4 py-3 text-right text-[12px] text-slate-500">
                    {formatRelative(m.last_activity_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        aria-label="Xem"
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-brand-indigo hover:bg-indigo-50"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        aria-label="Sửa"
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        aria-label="Khóa"
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-red-500 hover:bg-red-50"
                      >
                        <Ban className="h-4 w-4" />
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
    </main>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  tone: "indigo" | "orange" | "green";
}) {
  const toneClass =
    tone === "orange"
      ? "bg-orange-50 text-brand-orange"
      : tone === "green"
      ? "bg-emerald-50 text-emerald-600"
      : "bg-indigo-50 text-brand-indigo";
  const valueClass =
    tone === "orange" ? "text-brand-orange" : "text-slate-800";
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${toneClass}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <p className="text-[12px] text-slate-400">{label}</p>
      </div>
      <p
        className={`mt-3 font-headline text-[26px] font-bold ${valueClass}`}
      >
        {value}
      </p>
    </article>
  );
}
