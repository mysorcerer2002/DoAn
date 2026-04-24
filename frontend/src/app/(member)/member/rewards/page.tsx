"use client";

import { ArrowLeft, Crown, Gift, Loader2, Search } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useMe, useMyMemberships } from "@/lib/hooks/use-me";

interface MeRewardItem {
  id: number;
  tenant_id: number;
  tenant_name: string;
  tenant_slug: string;
  name: string;
  description: string | null;
  points_cost: number;
  stock: number | null;
  image_url: string | null;
  user_points_balance: number;
  can_redeem: boolean;
}

function useMyRewards() {
  return useQuery<MeRewardItem[]>({
    queryKey: ["member", "rewards"],
    queryFn: async () => (await api.get<MeRewardItem[]>("/users/me/rewards")).data,
  });
}

const FALLBACK_COLORS = [
  "bg-orange-50",
  "bg-indigo-50",
  "bg-violet-50",
  "bg-pink-50",
  "bg-amber-50",
  "bg-emerald-50",
];

function pickEmoji(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes("cafe") || lower.includes("latte")) return "☕";
  if (lower.includes("trà")) return "🍵";
  if (lower.includes("bánh")) return "🍰";
  if (lower.includes("voucher")) return "🎫";
  if (lower.includes("quà") || lower.includes("gift")) return "🎁";
  if (lower.includes("sữa")) return "🥤";
  if (lower.includes("topping")) return "✨";
  return "🎁";
}

export default function RewardsPage() {
  const { data: user } = useMe();
  const { data: memberships } = useMyMemberships();
  const { data: rewards, isLoading, isError } = useMyRewards();
  const [search, setSearch] = useState("");
  const [tenantFilter, setTenantFilter] = useState<number | null>(null);

  const tenants = useMemo(() => {
    const map = new Map<number, string>();
    (rewards ?? []).forEach((r) => map.set(r.tenant_id, r.tenant_name));
    return Array.from(map, ([id, name]) => ({ id, name }));
  }, [rewards]);

  const filtered = useMemo(() => {
    return (rewards ?? []).filter((r) => {
      if (tenantFilter != null && r.tenant_id !== tenantFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          r.name.toLowerCase().includes(q) ||
          r.tenant_name.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [rewards, tenantFilter, search]);

  const totalPoints =
    memberships?.reduce((sum, m) => sum + m.points_balance, 0) ?? 0;
  const topTier = (memberships ?? [])
    .slice()
    .sort((a, b) => b.points_balance - a.points_balance)[0];

  return (
    <>
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between bg-slate-50/95 px-4 backdrop-blur">
        <Link
          href="/member"
          className="flex h-10 w-10 items-center justify-center rounded-full text-brand-indigo hover:bg-indigo-50"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <h1 className="font-headline text-[18px] font-bold text-slate-800">
          Đổi quà
        </h1>
        <div className="w-10" />
      </header>

      <main className="space-y-4 px-4 pt-2 pb-8">
        {/* Hero điểm hiện có */}
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-indigo to-brand-violet p-4 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 flex items-center justify-between">
            <div>
              <p className="text-[12px] font-medium text-indigo-100">
                Điểm hiện có
              </p>
              <div className="flex items-baseline gap-2">
                <span className="font-headline text-[32px] font-bold leading-none text-brand-orange">
                  {totalPoints.toLocaleString("vi-VN")}
                </span>
                <span className="text-[12px] text-indigo-100">điểm</span>
              </div>
              <p className="mt-1 text-[10px] text-indigo-100/80">
                Tổng từ {memberships?.length ?? 0} đối tác
              </p>
            </div>
            {topTier?.current_tier_name && (
              <div className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
                <Crown className="h-3.5 w-3.5 text-white" fill="white" />
                <span className="font-headline text-[12px] font-bold text-white">
                  {topTier.current_tier_name}
                </span>
              </div>
            )}
          </div>
        </section>

        {/* Search */}
        <section className="relative">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm quà theo tên hoặc đối tác"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </section>

        {/* Tenant filter pills */}
        {tenants.length > 0 && (
          <section className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
            <button
              type="button"
              onClick={() => setTenantFilter(null)}
              className={
                tenantFilter === null
                  ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                  : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
              }
            >
              Tất cả ({rewards?.length ?? 0})
            </button>
            {tenants.map((t) => {
              const count = (rewards ?? []).filter(
                (r) => r.tenant_id === t.id
              ).length;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTenantFilter(t.id)}
                  className={
                    tenantFilter === t.id
                      ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                      : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
                  }
                >
                  {t.name} ({count})
                </button>
              );
            })}
          </section>
        )}

        {/* Rewards grid */}
        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-[13px] text-red-600">
            Không tải được danh sách quà
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
            <Gift className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              {search
                ? "Không tìm thấy quà phù hợp"
                : memberships?.length === 0
                  ? "Chưa có giao dịch tại đối tác nào"
                  : "Chưa có quà nào"}
            </p>
            {memberships?.length === 0 && (
              <Link
                href="/member/partners"
                className="mt-3 inline-block text-[13px] font-bold text-brand-indigo hover:underline"
              >
                Khám phá đối tác →
              </Link>
            )}
          </div>
        ) : (
          <section className="grid grid-cols-2 gap-3">
            {filtered.map((r, idx) => (
              <article
                key={r.id}
                className={
                  r.can_redeem
                    ? "relative overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm"
                    : "relative overflow-hidden rounded-2xl border border-slate-100 bg-white opacity-60 shadow-sm"
                }
              >
                {r.stock !== null && r.stock > 0 && r.stock <= 5 && (
                  <span className="absolute right-2 top-2 z-10 rounded-full bg-brand-orange px-2 py-0.5 text-[9px] font-bold text-white">
                    Còn {r.stock}
                  </span>
                )}
                <div
                  className={`flex aspect-square w-full items-center justify-center text-6xl ${FALLBACK_COLORS[idx % FALLBACK_COLORS.length]}`}
                >
                  {pickEmoji(r.name)}
                </div>
                <div className="space-y-1 p-3">
                  <h4 className="line-clamp-2 min-h-[2.4rem] font-headline text-[14px] font-bold leading-tight text-slate-800">
                    {r.name}
                  </h4>
                  <p className="truncate text-[11px] text-slate-400">
                    {r.tenant_name}
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="font-headline text-[14px] font-bold text-brand-orange">
                      {r.points_cost.toLocaleString("vi-VN")}đ
                    </span>
                    {r.can_redeem ? (
                      <button
                        type="button"
                        className="rounded-full bg-brand-indigo px-3 py-1 text-[11px] font-bold text-white shadow-sm active:scale-95"
                      >
                        Đổi
                      </button>
                    ) : (
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500">
                        Thiếu {(r.points_cost - r.user_points_balance).toLocaleString("vi-VN")}đ
                      </span>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>
    </>
  );
}
