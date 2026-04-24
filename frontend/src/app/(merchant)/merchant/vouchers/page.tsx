"use client";

import {
  CheckCircle2,
  Clock4,
  Percent,
  Ticket,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useMerchantVouchers } from "@/lib/hooks/use-partner";
import type { VoucherResponse } from "@/types/partner";

type Filter = "" | "issued" | "used" | "expired";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "", label: "Tất cả" },
  { key: "issued", label: "Còn hiệu lực" },
  { key: "used", label: "Đã dùng" },
  { key: "expired", label: "Hết hạn" },
];

function statusBadge(status: string) {
  if (status === "used")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-bold text-slate-600">
        <CheckCircle2 className="h-3 w-3" />
        Đã dùng
      </span>
    );
  if (status === "expired")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-bold text-red-600">
        <XCircle className="h-3 w-3" />
        Hết hạn
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-[11px] font-bold text-green-700">
      <Clock4 className="h-3 w-3" />
      Còn hiệu lực
    </span>
  );
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function fmtDiscount(v: VoucherResponse): string {
  if (!v.discount_value) return "—";
  return v.discount_type === "percent"
    ? `-${v.discount_value}%`
    : `-${v.discount_value.toLocaleString("vi-VN")}₫`;
}

export default function MerchantVouchersPage() {
  const [filter, setFilter] = useState<Filter>("");
  const { data, isLoading } = useMerchantVouchers({
    status: filter || undefined,
    limit: 200,
  });

  const stats = (data ?? []).reduce(
    (acc, v) => {
      acc.total += 1;
      if (v.status === "issued") acc.issued += 1;
      else if (v.status === "used") acc.used += 1;
      else if (v.status === "expired") acc.expired += 1;
      return acc;
    },
    { total: 0, issued: 0, used: 0, expired: 0 }
  );

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">
            Marketing / Quản lý voucher
          </p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Voucher đã phát
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Theo dõi voucher phát cho khách từ các chiến dịch khuyến mãi
          </p>
        </div>
        <Link
          href="/merchant/campaigns"
          className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-3 font-headline text-[13px] font-bold text-white shadow-lg shadow-indigo-200 hover:opacity-95"
        >
          Tạo chiến dịch mới
        </Link>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard
          color="indigo"
          label="Tổng phát hành"
          value={stats.total}
          icon={Ticket}
        />
        <StatCard
          color="green"
          label="Còn hiệu lực"
          value={stats.issued}
          icon={Clock4}
        />
        <StatCard
          color="violet"
          label="Đã sử dụng"
          value={stats.used}
          icon={CheckCircle2}
        />
        <StatCard
          color="red"
          label="Hết hạn"
          value={stats.expired}
          icon={XCircle}
        />
      </section>

      <section className="mt-6 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key || "all"}
            type="button"
            onClick={() => setFilter(f.key)}
            className={
              filter === f.key
                ? "rounded-xl bg-brand-indigo px-4 py-2 text-[13px] font-bold text-white"
                : "rounded-xl border border-slate-200 bg-white px-4 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50"
            }
          >
            {f.label}
          </button>
        ))}
      </section>

      <section className="mt-4 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center text-slate-400">
            Đang tải danh sách...
          </div>
        ) : !data || data.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-8 py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-50 text-brand-orange">
              <Ticket className="h-8 w-8" />
            </div>
            <p className="mt-4 font-headline text-[16px] font-bold text-slate-700">
              Chưa có voucher nào
            </p>
            <p className="mt-2 max-w-md text-[13px] text-slate-500">
              Tạo chiến dịch khuyến mãi để phát voucher cho khách hàng thành viên.
            </p>
            <Link
              href="/merchant/campaigns"
              className="mt-5 rounded-xl bg-brand-indigo px-5 py-2.5 text-[13px] font-bold text-white hover:opacity-95"
            >
              Đi tới Chiến dịch
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[800px] text-left text-[13px]">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-6 py-3">Mã voucher</th>
                <th className="px-6 py-3">Chiến dịch</th>
                <th className="px-6 py-3">Giảm giá</th>
                <th className="px-6 py-3">Phát hành</th>
                <th className="px-6 py-3">Hết hạn</th>
                <th className="px-6 py-3">Trạng thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <span className="rounded-lg bg-indigo-50 px-3 py-1.5 font-mono text-[13px] font-bold text-brand-indigo">
                      {v.code}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-700">
                    {v.campaign_name || `#${v.campaign_id}`}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 font-headline text-[14px] font-bold text-brand-orange">
                      <Percent className="h-3 w-3" />
                      {fmtDiscount(v)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {fmtDate(v.issued_at)}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {fmtDate(v.expires_at)}
                  </td>
                  <td className="px-6 py-4">{statusBadge(v.status)}</td>
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

const COLOR_MAP: Record<string, string> = {
  indigo: "bg-indigo-50 text-brand-indigo",
  violet: "bg-violet-50 text-brand-violet",
  green: "bg-green-50 text-green-600",
  red: "bg-red-50 text-red-600",
};

function StatCard({
  color,
  label,
  value,
  icon: Icon,
}: {
  color: string;
  label: string;
  value: number;
  icon: typeof Ticket;
}) {
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-xl ${COLOR_MAP[color] ?? COLOR_MAP.indigo}`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <p className="mt-3 font-headline text-[24px] font-bold text-slate-800">
        {value}
      </p>
      <p className="text-[12px] text-slate-500">{label}</p>
    </article>
  );
}
