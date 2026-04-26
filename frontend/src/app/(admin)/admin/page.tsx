"use client";

import {
  Activity,
  ArrowRight,
  Coins,
  CreditCard,
  Loader2,
  Shield,
  Store,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";

import { usePlatformStats } from "@/lib/hooks/use-partner";

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

      {/* Hero metric card — tổng giao dịch nổi bật gradient */}
      <section className="mt-6 overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-900 via-brand-indigo to-brand-violet p-6 text-white shadow-xl shadow-indigo-200 md:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-[11px] font-bold uppercase tracking-widest backdrop-blur">
              <Shield className="h-3 w-3" />
              Super Admin
            </div>
            <p className="mt-4 font-headline text-[16px] font-medium text-indigo-100">
              Tổng giao dịch toàn platform
            </p>
            <p className="mt-1 font-headline text-[56px] font-bold leading-none text-white">
              {data.total_transactions.toLocaleString("vi-VN")}
            </p>
            <div className="mt-3 flex items-center gap-2 text-[13px] text-indigo-100">
              <Activity className="h-4 w-4" />
              Dữ liệu real-time từ database
            </div>
          </div>
          <div className="grid flex-shrink-0 grid-cols-2 gap-3 md:min-w-[260px]">
            <HeroStat
              icon={Store}
              label="Đối tác"
              value={data.total_tenants.toLocaleString("vi-VN")}
            />
            <HeroStat
              icon={Users}
              label="Người dùng"
              value={data.total_users.toLocaleString("vi-VN")}
            />
          </div>
        </div>
      </section>

      {/* Secondary metrics + growth bars */}
      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SecondaryStat
          icon={Store}
          label="Đối tác đang hoạt động"
          value={data.total_tenants}
          tone="indigo"
          sub={`${data.total_tenants} đối tác tổng cộng`}
        />
        <SecondaryStat
          icon={Users}
          label="Tài khoản người dùng"
          value={data.total_users}
          tone="violet"
          sub="Bao gồm cả owner và customer"
        />
        <SecondaryStat
          icon={CreditCard}
          label="Giao dịch đã xử lý"
          value={data.total_transactions}
          tone="orange"
          sub="Lifetime count"
        />
        <SecondaryStat
          icon={Coins}
          label="Tổng điểm lưu hành"
          value={data.total_points_circulating}
          tone="green"
          sub="Điểm trong ví active users"
        />
      </section>

      {/* Quick actions */}
      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <ActionCard
          href="/admin/partners"
          icon={Store}
          iconBg="bg-indigo-50 text-brand-indigo"
          title="Quản lý đối tác"
          desc="Duyệt đăng ký, suspend, xem chi tiết từng đối tác"
        />
        <ActionCard
          href="/admin/stats"
          icon={TrendingUp}
          iconBg="bg-orange-50 text-brand-orange"
          title="Thống kê chi tiết"
          desc="Biểu đồ tăng trưởng toàn hệ thống"
        />
        <ActionCard
          href="/admin/users"
          icon={Users}
          iconBg="bg-violet-50 text-brand-violet"
          title="Người dùng platform"
          desc="Tìm kiếm theo email/SĐT, filter role"
        />
        <ActionCard
          href="/admin/audit"
          icon={Activity}
          iconBg="bg-green-50 text-green-600"
          title="Nhật ký hoạt động"
          desc="Timeline sự kiện gần đây trên platform"
        />
        <ActionCard
          href="/admin/logs"
          icon={CreditCard}
          iconBg="bg-slate-50 text-slate-600"
          title="Nhật ký đăng nhập"
          desc="Xem log đăng nhập và điều chỉnh điểm"
        />
        <ActionCard
          href="/admin/system-points"
          icon={Coins}
          iconBg="bg-indigo-50 text-brand-indigo"
          title="Quản lý điểm hệ thống"
          desc="Tổng quan điểm lưu hành toàn nền tảng"
        />
      </section>
    </main>
  );
}

function HeroStat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Store;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15">
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-3 font-headline text-[24px] font-bold leading-none">
        {value}
      </p>
      <p className="mt-1 text-[11px] text-indigo-100">{label}</p>
    </div>
  );
}

function SecondaryStat({
  icon: Icon,
  label,
  value,
  tone,
  sub,
}: {
  icon: typeof Store;
  label: string;
  value: number;
  tone: "indigo" | "violet" | "orange" | "green";
  sub: string;
}) {
  const toneClass: Record<string, string> = {
    indigo: "bg-indigo-50 text-brand-indigo",
    violet: "bg-violet-50 text-brand-violet",
    orange: "bg-orange-50 text-brand-orange",
    green: "bg-green-50 text-green-600",
  };
  const barClass: Record<string, string> = {
    indigo: "bg-brand-indigo",
    violet: "bg-brand-violet",
    orange: "bg-brand-orange",
    green: "bg-green-500",
  };
  // Visual only — width based on value (log scale)
  const width = Math.min(100, Math.max(5, Math.log10(value + 1) * 30));
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${toneClass[tone]}`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-4 text-[12px] font-medium text-slate-400">{label}</p>
      <p className="mt-1 font-headline text-[28px] font-bold text-slate-800">
        {value.toLocaleString("vi-VN")}
      </p>
      <p className="mt-1 text-[11px] text-slate-400">{sub}</p>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${barClass[tone]}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </article>
  );
}

function ActionCard({
  href,
  icon: Icon,
  iconBg,
  title,
  desc,
}: {
  href: string;
  icon: typeof Store;
  iconBg: string;
  title: string;
  desc: string;
}) {
  return (
    <Link
      href={href}
      className="group flex items-center justify-between rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:border-brand-indigo hover:shadow-lg"
    >
      <div className="flex items-center gap-4">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-xl ${iconBg}`}
        >
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <h3 className="font-headline text-[16px] font-bold text-slate-800">
            {title}
          </h3>
          <p className="mt-0.5 text-[12px] text-slate-500">{desc}</p>
        </div>
      </div>
      <ArrowRight className="h-5 w-5 flex-shrink-0 text-slate-300 transition-transform group-hover:translate-x-1 group-hover:text-brand-indigo" />
    </Link>
  );
}
