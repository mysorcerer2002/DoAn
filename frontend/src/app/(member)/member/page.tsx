"use client";

import {
  Bell,
  Clock,
  Crown,
  Gift,
  History,
  Loader2,
  QrCode,
  Ticket,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useMyVouchers } from "@/lib/hooks/use-partner";
import { useMe, useMyMemberships } from "@/lib/hooks/use-me";
import type { Membership } from "@/types/auth";

const quickActions = [
  { id: "qr", icon: QrCode, label: "Mã QR", href: "/member/qr", color: "indigo" },
  { id: "redeem", icon: Gift, label: "Đổi quà", href: "/member/rewards", color: "orange" },
  {
    id: "voucher",
    icon: Ticket,
    label: "Voucher",
    href: "/member/vouchers",
    color: "orange",
  },
  {
    id: "history",
    icon: History,
    label: "Lịch sử",
    href: "/member/history",
    color: "indigo",
  },
] as const;

function getInitials(fullName: string | null): string {
  if (!fullName) return "M";
  const parts = fullName.trim().split(/\s+/);
  return parts
    .slice(-2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

function getFirstName(fullName: string | null): string {
  if (!fullName) return "bạn";
  const parts = fullName.trim().split(/\s+/);
  return parts[parts.length - 1] ?? "bạn";
}

function computeTotalPoints(memberships: Membership[]): number {
  return memberships.reduce((sum, m) => sum + m.points_balance, 0);
}

function formatVnPoints(n: number): string {
  return n.toLocaleString("vi-VN");
}

const TIER_EMOJI: Record<string, string> = {
  "Hạng Đồng": "🥉",
  "Hạng Bạc": "🥈",
  "Hạng Vàng": "🥇",
  "Hạng Bạch Kim": "💎",
};

export default function MemberDashboardPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const { data: user, isLoading: isLoadingUser, isError: isErrorUser } = useMe();
  const { data: memberships, isLoading: isLoadingMemberships } =
    useMyMemberships();
  const { data: vouchers } = useMyVouchers({ status: "issued" });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && isErrorUser) {
      router.replace("/login");
    }
  }, [mounted, isErrorUser, router]);

  if (!mounted || isLoadingUser || isLoadingMemberships) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const totalPoints = computeTotalPoints(memberships ?? []);
  const topMembership = (memberships ?? [])
    .slice()
    .sort((a, b) => b.points_balance - a.points_balance)[0];
  const topTierName = topMembership?.current_tier_name ?? "Thành viên mới";
  const shopCount = memberships?.length ?? 0;

  return (
    <>
      {/* TopAppBar */}
      <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between bg-slate-50/95 px-4 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 overflow-hidden rounded-full border-2 border-indigo-100 bg-gradient-to-br from-indigo-200 to-violet-200">
            <div className="flex h-full w-full items-center justify-center text-lg font-bold text-indigo-700">
              {getInitials(user.full_name)}
            </div>
          </div>
          <h1 className="font-headline text-[16px] font-bold text-slate-800">
            Chào, {getFirstName(user.full_name)} ☀️
          </h1>
        </div>
        <button
          type="button"
          className="group relative cursor-pointer transition-opacity hover:opacity-80"
          aria-label="Thông báo"
        >
          <Bell className="h-6 w-6 text-brand-indigo" />
        </button>
      </header>

      <main className="space-y-6 px-4 pt-2">
        {/* Hero Points Card */}
        <section className="relative overflow-hidden rounded-[20px] bg-gradient-to-br from-brand-indigo to-brand-violet p-6 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 space-y-4">
            <div className="flex items-start justify-between">
              <p className="font-headline text-[12px] font-extrabold uppercase tracking-widest text-indigo-100/80">
                TỔNG ĐIỂM TÍCH LŨY
              </p>
              <div className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
                <Crown className="h-3.5 w-3.5 text-white" fill="white" />
                <span className="font-headline text-[12px] font-bold text-white">
                  {topTierName}
                </span>
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-headline text-glow-orange text-[64px] font-bold leading-none text-brand-orange">
                {formatVnPoints(totalPoints)}
              </span>
              <span className="font-medium text-indigo-100">điểm</span>
            </div>
            <div className="space-y-2">
              <p className="text-[12px] font-medium text-indigo-50">
                {shopCount > 0
                  ? `Tích lũy tại ${shopCount} đối tác`
                  : "Quét QR đối tác để bắt đầu tích điểm"}
              </p>
            </div>
          </div>
        </section>

        {/* Quick Actions */}
        <section className="grid grid-cols-4 gap-3">
          {quickActions.map(({ id, icon: Icon, label, href, color }) => (
            <Link key={id} href={href} className="group flex flex-col items-center gap-2">
              <div className="flex aspect-square w-full items-center justify-center rounded-2xl border border-slate-100 bg-white shadow-sm transition-transform group-active:scale-95">
                <Icon
                  className={
                    color === "indigo"
                      ? "h-6 w-6 text-brand-indigo"
                      : "h-6 w-6 text-brand-orange"
                  }
                />
              </div>
              <span className="text-[11px] font-medium text-slate-600">{label}</span>
            </Link>
          ))}
        </section>

        {/* Favorite Stores (real data) */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-headline text-[18px] font-bold text-slate-800">
              Đối tác của tôi
            </h3>
            <Link
              href="/member/partners"
              className="text-[14px] font-semibold text-brand-indigo hover:underline"
            >
              Khám phá
            </Link>
          </div>
          {shopCount === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center">
              <p className="text-[14px] text-slate-500">
                Chưa có giao dịch tại đối tác nào. Khám phá đối tác để bắt đầu tích điểm.
              </p>
              <Link
                href="/member/partners"
                className="mt-3 inline-block text-[13px] font-bold text-brand-indigo hover:underline"
              >
                Khám phá đối tác →
              </Link>
            </div>
          ) : (
            <div className="no-scrollbar -mx-4 flex gap-4 overflow-x-auto px-4 pb-4">
              {memberships!.map((m) => (
                <div
                  key={m.membership_id}
                  className="min-w-[180px] shrink-0 space-y-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-2xl shadow-inner">
                    {TIER_EMOJI[m.current_tier_name ?? ""] ?? "🏪"}
                  </div>
                  <div className="space-y-1">
                    <h4 className="truncate text-[14px] font-bold text-slate-800">
                      Đối tác #{m.tenant_id}
                    </h4>
                    <p className="truncate text-[12px] text-slate-400">
                      {m.current_tier_name ?? "Chưa phân hạng"}
                    </p>
                  </div>
                  <div className="flex items-center justify-between border-t border-slate-50 pt-2">
                    <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold uppercase text-indigo-500">
                      Thành viên
                    </span>
                    <span className="text-[14px] font-bold text-brand-orange">
                      {formatVnPoints(m.points_balance)} đ
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Voucher khả dụng (real data) */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-headline text-[18px] font-bold text-slate-800">
              Voucher khả dụng
            </h3>
            {vouchers && vouchers.length > 0 && (
              <Link
                href="/member/vouchers"
                className="text-[13px] font-semibold text-brand-indigo hover:underline"
              >
                Xem tất cả
              </Link>
            )}
          </div>
          {!vouchers || vouchers.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center">
              <Ticket className="mx-auto h-10 w-10 text-slate-300" />
              <p className="mt-3 text-[13px] text-slate-500">
                Chưa có voucher nào. Tích điểm để nhận voucher từ đối tác.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {vouchers.slice(0, 3).map((v) => {
                const valueLabel =
                  v.discount_type === "percent"
                    ? `${v.discount_value}%`
                    : `${(v.discount_value ?? 0).toLocaleString("vi-VN")}₫`;
                return (
                  <article
                    key={v.id}
                    className="relative flex items-center overflow-hidden rounded-2xl border-l-4 border-brand-orange bg-white shadow-sm"
                  >
                    <span className="absolute -top-1 left-24 h-4 w-4 rounded-full border border-slate-100 bg-[#f8fafc]" />
                    <span className="absolute -bottom-1 left-24 h-4 w-4 rounded-full border border-slate-100 bg-[#f8fafc]" />
                    <div className="flex-1 p-4">
                      <h4 className="text-[15px] font-bold text-slate-800">
                        {v.campaign_name ?? `Voucher ${v.code}`}
                      </h4>
                      <p className="font-mono text-[11px] text-slate-500">
                        Mã: {v.code}
                      </p>
                      <p className="mt-2 flex items-center gap-1 text-[11px] text-slate-400">
                        <Clock className="h-3.5 w-3.5" />
                        Hết hạn{" "}
                        {new Date(v.expires_at).toLocaleDateString("vi-VN", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                    <div className="flex min-w-[100px] flex-col items-center justify-center border-l border-dashed border-slate-200 bg-slate-50/50 p-4">
                      <span className="text-glow-orange text-[24px] font-bold text-brand-orange">
                        -{valueLabel}
                      </span>
                      <span className="mt-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                        {v.discount_type === "percent" ? "giảm" : "off"}
                      </span>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </>
  );
}
