"use client";

import Link from "next/link";
import { CreditCard, Mail, Phone, Store, Ticket, User } from "lucide-react";

import { useMe } from "@/lib/hooks/use-me";
import { usePartnerStore } from "@/lib/partner-store";

export default function StaffDashboardPage() {
  const { data: user } = useMe();
  const partner = usePartnerStore((s) => s.activePartner);

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Cửa hàng / Trang chủ</p>
        <h1 className="mt-1 font-headline text-[28px] font-bold text-slate-800 md:text-[32px]">
          Xin chào{user?.full_name ? `, ${user.full_name}` : ""} 👋
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Chọn thao tác bạn muốn thực hiện tại quầy.
        </p>
      </header>

      {/* Quick actions */}
      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          href="/staff/pos/transactions/new"
          className="group flex items-center gap-4 rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
        >
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-sm group-hover:bg-emerald-700">
            <CreditCard className="h-7 w-7" />
          </div>
          <div>
            <p className="font-headline text-[18px] font-bold text-slate-800">
              Tích điểm
            </p>
            <p className="mt-0.5 text-[13px] text-slate-500">
              Tạo giao dịch và cộng điểm cho khách
            </p>
          </div>
        </Link>

        <Link
          href="/staff/pos/redemptions/use"
          className="group flex items-center gap-4 rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
        >
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-amber-500 text-white shadow-sm group-hover:bg-amber-600">
            <Ticket className="h-7 w-7" />
          </div>
          <div>
            <p className="font-headline text-[18px] font-bold text-slate-800">
              Dùng voucher
            </p>
            <p className="mt-0.5 text-[13px] text-slate-500">
              Quét QR hoặc nhập mã 8 ký tự
            </p>
          </div>
        </Link>
      </section>

      {/* Staff info */}
      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-[12px] font-bold uppercase tracking-wide text-slate-400">
          Thông tin nhân viên
        </h2>
        <div className="space-y-3 text-[14px]">
          <InfoRow icon={User} label="Họ tên" value={user?.full_name ?? "—"} />
          <InfoRow icon={Mail} label="Email" value={user?.email ?? "—"} />
          <InfoRow icon={Phone} label="SĐT" value={user?.phone ?? "—"} />
          <InfoRow
            icon={Store}
            label="Cửa hàng"
            value={partner?.name ?? "—"}
          />
        </div>
      </section>
    </main>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[11px] uppercase tracking-wide text-slate-400">
          {label}
        </p>
        <p className="truncate font-medium text-slate-700">{value}</p>
      </div>
    </div>
  );
}
