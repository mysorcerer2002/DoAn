"use client";

import {
  ArrowRight,
  CreditCard,
  Loader2,
  Store,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";

import { StatCard } from "@/components/ui/stat-card";
import { usePlatformStats } from "@/lib/hooks/use-merchant";

export default function AdminDashboardPage() {
  const { data, isLoading, isError } = usePlatformStats();

  if (isLoading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  if (isError || !data) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center px-8">
        <p className="text-red-600">Không tải được thống kê platform</p>
      </main>
    );
  }

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Hệ thống / Tổng quan</p>
        <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
          Tổng quan hệ thống
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Theo dõi hoạt động toàn nền tảng Loyalty Platform
        </p>
      </header>

      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          icon={Store}
          label="Tổng đối tác"
          value={data.total_tenants.toLocaleString("vi-VN")}
          tone="indigo"
        />
        <StatCard
          icon={Users}
          label="Tổng người dùng"
          value={data.total_users.toLocaleString("vi-VN")}
          tone="indigo"
        />
        <StatCard
          icon={CreditCard}
          label="Tổng giao dịch"
          value={data.total_transactions.toLocaleString("vi-VN")}
          tone="orange"
          highlightValue
        />
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          href="/admin/tenants"
          className="group flex items-center justify-between rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:border-brand-indigo hover:shadow-lg"
        >
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-brand-indigo">
              <Store className="h-6 w-6" />
            </div>
            <h3 className="mt-3 font-headline text-[18px] font-bold text-slate-800">
              Quản lý đối tác
            </h3>
            <p className="mt-1 text-[13px] text-slate-500">
              Duyệt đăng ký, suspend, xem chi tiết
            </p>
          </div>
          <ArrowRight className="h-6 w-6 text-slate-300 transition-transform group-hover:translate-x-1 group-hover:text-brand-indigo" />
        </Link>

        <Link
          href="/admin/stats"
          className="group flex items-center justify-between rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:border-brand-indigo hover:shadow-lg"
        >
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-50 text-brand-orange">
              <TrendingUp className="h-6 w-6" />
            </div>
            <h3 className="mt-3 font-headline text-[18px] font-bold text-slate-800">
              Thống kê chi tiết
            </h3>
            <p className="mt-1 text-[13px] text-slate-500">
              Xem báo cáo toàn hệ thống
            </p>
          </div>
          <ArrowRight className="h-6 w-6 text-slate-300 transition-transform group-hover:translate-x-1 group-hover:text-brand-indigo" />
        </Link>
      </section>
    </main>
  );
}
