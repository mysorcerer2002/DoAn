"use client";

import { ArrowLeft, Clock, Loader2, Search, Ticket } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { useMyVouchers } from "@/lib/hooks/use-merchant";
import type { VoucherResponse } from "@/types/merchant";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function daysLeft(iso: string): number {
  const diff = new Date(iso).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

const TABS = [
  { id: "issued", label: "Khả dụng" },
  { id: "used", label: "Đã dùng" },
  { id: "expired", label: "Hết hạn" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function VouchersPage() {
  const [tab, setTab] = useState<TabId>("issued");
  const { data: vouchers, isLoading, isError } = useMyVouchers({ status: tab });

  const counts = useMemo(() => {
    return {
      issued: vouchers?.filter((v) => v.status === "issued").length ?? 0,
      used: vouchers?.filter((v) => v.status === "used").length ?? 0,
      expired: vouchers?.filter((v) => v.status === "expired").length ?? 0,
    };
  }, [vouchers]);

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
          Voucher của tôi
        </h1>
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-brand-indigo hover:bg-indigo-50"
          aria-label="Tìm kiếm"
        >
          <Search className="h-6 w-6" />
        </button>
      </header>

      <main className="space-y-4 px-4 pt-2">
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-indigo to-brand-violet p-4 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 space-y-1">
            <p className="text-[14px] font-bold text-white">
              {counts.issued} voucher khả dụng
            </p>
            <p className="text-[12px] text-indigo-100">
              {counts.used} đã dùng · {counts.expired} hết hạn
            </p>
          </div>
        </section>

        <section className="flex items-center gap-2 overflow-x-auto pb-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={
                t.id === tab
                  ? "shrink-0 rounded-full bg-brand-indigo/10 px-4 py-2 text-[12px] font-bold text-brand-indigo"
                  : "shrink-0 rounded-full border border-slate-200 bg-white px-4 py-2 text-[12px] font-medium text-slate-500"
              }
            >
              {t.label}
            </button>
          ))}
        </section>

        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-red-600">
            Không tải được voucher
          </div>
        ) : vouchers?.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
            <Ticket className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              Chưa có voucher {tab === "issued" ? "khả dụng" : tab === "used" ? "đã dùng" : "hết hạn"}
            </p>
          </div>
        ) : (
          <section className="space-y-3 pb-8">
            {vouchers?.map((v: VoucherResponse) => {
              const days = daysLeft(v.expires_at);
              const isExpired = v.status === "expired" || days === 0;
              return (
                <Link
                  key={v.id}
                  href={`/member/vouchers/${v.id}`}
                  className="relative flex w-full items-stretch overflow-hidden rounded-2xl border-l-4 border-brand-orange bg-white text-left shadow-sm transition active:scale-[0.99]"
                >
                  <div className="flex w-[100px] shrink-0 items-center justify-center bg-orange-50">
                    <Ticket className="h-9 w-9 text-brand-orange" />
                  </div>
                  <div className="flex-1 p-4">
                    <h3 className="font-headline text-[16px] font-bold text-slate-800">
                      {v.campaign_name ?? "Voucher"}
                    </h3>
                    <p className="font-mono text-[11px] text-slate-500">
                      {v.code}
                    </p>
                    <p className="mt-1 text-[11px] font-medium text-brand-indigo">
                      {v.discount_type === "percent"
                        ? `Giảm ${v.discount_value ?? "-"}%`
                        : v.discount_value
                        ? `Giảm ${v.discount_value.toLocaleString("vi-VN")}₫`
                        : ""}
                    </p>
                    <div className="mt-2 flex items-center gap-1 text-[10px] text-slate-400">
                      <Clock className="h-3 w-3" />
                      {v.status === "used"
                        ? `Đã dùng: ${v.used_at ? formatDate(v.used_at) : "—"}`
                        : isExpired
                          ? `Hết hạn: ${formatDate(v.expires_at)}`
                          : `Còn ${days} ngày (${formatDate(v.expires_at)})`}
                    </div>
                    <p className="mt-2 text-[10px] font-bold text-brand-indigo">
                      Xem chi tiết →
                    </p>
                  </div>
                </Link>
              );
            })}
          </section>
        )}
      </main>

    </>
  );
}
