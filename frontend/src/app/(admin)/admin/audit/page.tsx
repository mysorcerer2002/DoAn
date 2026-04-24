"use client";

import {
  Activity,
  Building2,
  CheckCircle2,
  Receipt,
  ShieldOff,
  UserPlus,
} from "lucide-react";

import { useAdminAuditFeed } from "@/lib/hooks/use-partner";
import type { AuditFeedItem } from "@/types/partner";

const EVENT_META: Record<
  AuditFeedItem["event_type"],
  { icon: typeof Activity; color: string; label: string }
> = {
  tenant_created: {
    icon: Building2,
    color: "bg-indigo-50 text-brand-indigo",
    label: "Tenant mới",
  },
  tenant_approved: {
    icon: CheckCircle2,
    color: "bg-green-50 text-green-600",
    label: "Đã duyệt",
  },
  tenant_suspended: {
    icon: ShieldOff,
    color: "bg-red-50 text-red-600",
    label: "Đình chỉ",
  },
  user_registered: {
    icon: UserPlus,
    color: "bg-violet-50 text-brand-violet",
    label: "Đăng ký",
  },
  transaction: {
    icon: Receipt,
    color: "bg-orange-50 text-brand-orange",
    label: "Giao dịch",
  },
};

function fmtRelative(iso: string): string {
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AdminAuditPage() {
  const { data: items, isLoading, isError } = useAdminAuditFeed(50);

  const counts = (items ?? []).reduce(
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
          <p className="text-[12px] text-slate-400">Hệ thống / Nhật ký</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Nhật ký hoạt động
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            {items?.length ?? 0} sự kiện gần đây trên toàn platform
          </p>
        </div>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatPill icon={Building2} label="Tenants" value={(counts.tenant_created ?? 0) + (counts.tenant_approved ?? 0) + (counts.tenant_suspended ?? 0)} color="indigo" />
        <StatPill icon={UserPlus} label="Đăng ký" value={counts.user_registered ?? 0} color="violet" />
        <StatPill icon={Receipt} label="Giao dịch" value={counts.transaction ?? 0} color="orange" />
        <StatPill icon={CheckCircle2} label="Duyệt" value={counts.tenant_approved ?? 0} color="green" />
        <StatPill icon={ShieldOff} label="Đình chỉ" value={counts.tenant_suspended ?? 0} color="red" />
      </section>

      <section className="mt-8">
        {isLoading ? (
          <div className="rounded-2xl border border-slate-100 bg-white p-12 text-center text-slate-400 shadow-sm">
            Đang tải nhật ký...
          </div>
        ) : isError ? (
          <div className="rounded-2xl border border-red-100 bg-red-50 p-6 text-center text-red-600 shadow-sm">
            Không tải được nhật ký
          </div>
        ) : !items || items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-16 text-center">
            <Activity className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">Chưa có hoạt động nào</p>
          </div>
        ) : (
          <ol className="relative space-y-1 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <div
              className="absolute left-[38px] top-6 bottom-6 w-px bg-slate-100"
              aria-hidden="true"
            />
            {items.map((item, idx) => {
              const meta = EVENT_META[item.event_type] ?? EVENT_META.transaction;
              const Icon = meta.icon;
              return (
                <li key={idx} className="relative flex gap-4 py-4">
                  <div
                    className={`z-10 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl ${meta.color}`}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${meta.color}`}>
                        {meta.label}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {fmtRelative(item.at)}
                      </span>
                    </div>
                    <h3 className="mt-1 font-headline text-[15px] font-bold text-slate-800">
                      {item.title}
                    </h3>
                    {item.description && (
                      <p className="mt-0.5 text-[12px] text-slate-500">
                        {item.description}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </section>
    </main>
  );
}

const COLOR_MAP: Record<string, string> = {
  indigo: "bg-indigo-50 text-brand-indigo",
  violet: "bg-violet-50 text-brand-violet",
  orange: "bg-orange-50 text-brand-orange",
  green: "bg-green-50 text-green-600",
  red: "bg-red-50 text-red-600",
};

function StatPill({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Activity;
  label: string;
  value: number;
  color: keyof typeof COLOR_MAP | string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${COLOR_MAP[color] ?? COLOR_MAP.indigo}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="font-headline text-[20px] font-bold text-slate-800">
          {value}
        </p>
        <p className="text-[11px] text-slate-400">{label}</p>
      </div>
    </div>
  );
}
