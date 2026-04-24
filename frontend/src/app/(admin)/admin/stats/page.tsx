"use client";

import {
  Activity,
  Building2,
  CheckCircle2,
  CreditCard,
  Loader2,
  Shield,
  ShieldAlert,
  Store,
  TrendingUp,
  Users,
} from "lucide-react";

import {
  useAdminAuditFeed,
  useAdminTenants,
  useAdminUsers,
  usePlatformStats,
} from "@/lib/hooks/use-partner";
import type { AuditFeedItem } from "@/types/partner";

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  return `${days} ngày trước`;
}

export default function AdminStatsPage() {
  const { data: stats, isLoading: isLoadingStats } = usePlatformStats();
  const { data: tenants, isLoading: isLoadingTenants } = useAdminTenants(undefined);
  const { data: usersData, isLoading: isLoadingUsers } = useAdminUsers({ limit: 200 });
  const { data: auditFeed, isLoading: isLoadingFeed } = useAdminAuditFeed(20);

  const isLoading =
    isLoadingStats || isLoadingTenants || isLoadingUsers || isLoadingFeed;

  if (isLoading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  if (!stats) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center px-8">
        <p className="text-red-600">Không tải được thống kê platform</p>
      </main>
    );
  }

  const tenantStatusCount = {
    active: tenants?.filter((t) => t.status === "active").length ?? 0,
    pending: tenants?.filter((t) => t.status === "pending").length ?? 0,
    suspended: tenants?.filter((t) => t.status === "suspended").length ?? 0,
  };

  const roleCount = {
    super_admin:
      usersData?.items.filter((u) => u.system_role === "super_admin").length ?? 0,
    admin: usersData?.items.filter((u) => u.system_role === "admin").length ?? 0,
    regular:
      usersData?.items.filter((u) => u.system_role === "regular").length ?? 0,
  };

  const eventCount = (auditFeed ?? []).reduce(
    (acc, item) => {
      acc[item.event_type] = (acc[item.event_type] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Hệ thống / Thống kê</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Thống kê hệ thống
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Tất cả số liệu real-time từ database, không mock data
          </p>
        </div>
      </header>

      {/* 3 hero metrics */}
      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <HeroStatCard
          icon={Store}
          label="Tổng đối tác"
          value={stats.total_tenants}
          sub={`${tenantStatusCount.active} đang hoạt động · ${tenantStatusCount.pending} chờ duyệt`}
          tone="indigo"
        />
        <HeroStatCard
          icon={Users}
          label="Tổng người dùng"
          value={stats.total_users}
          sub={`${roleCount.regular} user · ${roleCount.super_admin} admin`}
          tone="violet"
        />
        <HeroStatCard
          icon={CreditCard}
          label="Tổng giao dịch"
          value={stats.total_transactions}
          sub="Lifetime count toàn platform"
          tone="orange"
        />
      </section>

      {/* Trạng thái đối tác + Phân bố vai trò */}
      <section className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <header className="mb-5">
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Trạng thái đối tác
            </h2>
            <p className="text-[12px] text-slate-400">
              Phân bố {stats.total_tenants} đối tác theo trạng thái
            </p>
          </header>
          <DistributionBar
            items={[
              {
                label: "Đang hoạt động",
                count: tenantStatusCount.active,
                color: "bg-emerald-500",
                icon: CheckCircle2,
              },
              {
                label: "Chờ duyệt",
                count: tenantStatusCount.pending,
                color: "bg-amber-500",
                icon: Activity,
              },
              {
                label: "Tạm dừng",
                count: tenantStatusCount.suspended,
                color: "bg-red-500",
                icon: Building2,
              },
            ]}
            total={stats.total_tenants}
          />
        </article>

        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <header className="mb-5">
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Phân bố vai trò
            </h2>
            <p className="text-[12px] text-slate-400">
              {usersData?.total ?? 0} tài khoản platform
            </p>
          </header>
          <DistributionBar
            items={[
              {
                label: "Super Admin",
                count: roleCount.super_admin,
                color: "bg-red-500",
                icon: ShieldAlert,
              },
              {
                label: "Admin",
                count: roleCount.admin,
                color: "bg-brand-indigo",
                icon: Shield,
              },
              {
                label: "Người dùng",
                count: roleCount.regular,
                color: "bg-slate-400",
                icon: Users,
              },
            ]}
            total={usersData?.total ?? 0}
          />
        </article>
      </section>

      {/* Event counts + Recent activity */}
      <section className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-1">
          <header className="mb-5">
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Sự kiện gần đây
            </h2>
            <p className="text-[12px] text-slate-400">
              {auditFeed?.length ?? 0} sự kiện trong 20 gần nhất
            </p>
          </header>
          <ul className="space-y-3">
            <EventRow
              label="Đối tác được duyệt"
              count={eventCount.tenant_approved ?? 0}
              color="text-emerald-600"
            />
            <EventRow
              label="Đối tác bị đình chỉ"
              count={eventCount.tenant_suspended ?? 0}
              color="text-red-600"
            />
            <EventRow
              label="Đối tác mới"
              count={eventCount.tenant_created ?? 0}
              color="text-brand-indigo"
            />
            <EventRow
              label="Đăng ký user"
              count={eventCount.user_registered ?? 0}
              color="text-brand-violet"
            />
            <EventRow
              label="Giao dịch"
              count={eventCount.transaction ?? 0}
              color="text-brand-orange"
            />
          </ul>
        </article>

        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-2">
          <header className="mb-5">
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Hoạt động gần đây
            </h2>
            <p className="text-[12px] text-slate-400">
              Timeline sự kiện từ audit feed
            </p>
          </header>
          {!auditFeed || auditFeed.length === 0 ? (
            <div className="flex h-40 items-center justify-center text-[13px] text-slate-400">
              Chưa có sự kiện nào
            </div>
          ) : (
            <ol className="space-y-3">
              {auditFeed.slice(0, 8).map((item: AuditFeedItem, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-brand-indigo" />
                  <div className="flex-1 border-b border-slate-50 pb-3 last:border-0">
                    <p className="text-[13px] font-bold text-slate-800">
                      {item.title}
                    </p>
                    {item.description && (
                      <p className="text-[11px] text-slate-500">
                        {item.description}
                      </p>
                    )}
                    <p className="mt-0.5 text-[10px] text-slate-400">
                      {formatRelative(item.at)}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </article>
      </section>

      {/* Top tenants list */}
      <section className="mt-6 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <header className="mb-5">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Danh sách đối tác
          </h2>
          <p className="text-[12px] text-slate-400">
            Tất cả đối tác trên platform
          </p>
        </header>
        {!tenants || tenants.length === 0 ? (
          <div className="flex h-20 items-center justify-center text-[13px] text-slate-400">
            Chưa có đối tác nào
          </div>
        ) : (
          <ul className="space-y-2">
            {tenants.map((t, idx) => (
              <li
                key={t.id}
                className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 font-bold text-brand-indigo">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="font-bold text-slate-800">{t.name}</p>
                    <p className="font-mono text-[11px] text-slate-400">
                      {t.slug}
                    </p>
                  </div>
                </div>
                <span
                  className={
                    t.status === "active"
                      ? "rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-600"
                      : t.status === "pending"
                        ? "rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-700"
                        : "rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-bold text-red-600"
                  }
                >
                  {t.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

const TONE_CLASS: Record<string, string> = {
  indigo: "from-brand-indigo to-indigo-700 text-white",
  violet: "from-brand-violet to-purple-700 text-white",
  orange: "from-brand-orange to-amber-600 text-white",
};

function HeroStatCard({
  icon: Icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: typeof Store;
  label: string;
  value: number;
  sub: string;
  tone: keyof typeof TONE_CLASS;
}) {
  return (
    <article
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br p-6 shadow-lg ${TONE_CLASS[tone]}`}
    >
      <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
      <div className="relative z-10 flex items-start justify-between">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
          <Icon className="h-6 w-6" />
        </div>
      </div>
      <p className="relative z-10 mt-4 text-[12px] font-medium uppercase tracking-wider text-white/80">
        {label}
      </p>
      <p className="relative z-10 mt-1 font-headline text-[40px] font-bold leading-none">
        {value.toLocaleString("vi-VN")}
      </p>
      <p className="relative z-10 mt-2 text-[11px] text-white/80">{sub}</p>
    </article>
  );
}

function DistributionBar({
  items,
  total,
}: {
  items: { label: string; count: number; color: string; icon: typeof Store }[];
  total: number;
}) {
  return (
    <div className="space-y-3">
      {items.map((item) => {
        const percent = total > 0 ? (item.count / total) * 100 : 0;
        const Icon = item.icon;
        return (
          <div key={item.label}>
            <div className="mb-1 flex items-center justify-between text-[13px]">
              <span className="flex items-center gap-2 font-medium text-slate-700">
                <Icon className="h-3.5 w-3.5" />
                {item.label}
              </span>
              <span className="font-bold text-slate-800">
                {item.count} · {percent.toFixed(0)}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${item.color}`}
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function EventRow({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: string;
}) {
  return (
    <li className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
      <span className="text-[13px] text-slate-600">{label}</span>
      <span className={`font-headline text-[20px] font-bold ${color}`}>
        {count}
      </span>
    </li>
  );
}
