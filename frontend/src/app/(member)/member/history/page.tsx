"use client";

import { ArrowLeft, Filter, Gift, History, Loader2, Sparkles } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";

import { useMyLedger } from "@/lib/hooks/use-partner";
import type { LedgerEntryResponse } from "@/types/partner";

function formatRelative(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
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
  });
}

function reasonIcon(reason: string) {
  if (reason === "redeem") return Gift;
  if (reason === "adjust") return Sparkles;
  return History;
}

function reasonLabel(reason: string): string {
  const map: Record<string, string> = {
    earn: "Tích điểm",
    redeem: "Đổi quà",
    adjust: "Điều chỉnh",
    refund: "Hoàn điểm",
    expire: "Hết hạn",
  };
  return map[reason] ?? reason;
}

export default function HistoryPage() {
  const { data: entries, isLoading, isError } = useMyLedger({ limit: 100 });

  const totals = useMemo(() => {
    if (!entries) return { earned: 0, redeemed: 0, count: 0 };
    let earned = 0;
    let redeemed = 0;
    entries.forEach((e) => {
      if (e.delta > 0) earned += e.delta;
      else redeemed += Math.abs(e.delta);
    });
    return { earned, redeemed, count: entries.length };
  }, [entries]);

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
          Lịch sử tích điểm
        </h1>
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-brand-indigo hover:bg-indigo-50"
          aria-label="Lọc"
        >
          <Filter className="h-6 w-6" />
        </button>
      </header>

      <main className="space-y-5 px-4 pt-2">
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-indigo to-brand-violet p-5 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 space-y-2">
            <p className="text-[12px] font-medium text-indigo-100">
              Tổng đã tích lũy
            </p>
            <p className="font-headline text-[36px] font-bold text-brand-orange text-glow-orange leading-none">
              +{totals.earned.toLocaleString("vi-VN")}
            </p>
            <p className="text-[12px] text-indigo-50/80">
              Từ {totals.count} hoạt động (đã đổi {totals.redeemed.toLocaleString("vi-VN")} điểm)
            </p>
          </div>
        </section>

        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-red-600">
            Không tải được lịch sử
          </div>
        ) : entries?.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
            <History className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">Chưa có hoạt động</p>
            <p className="mt-2 text-[13px] text-slate-500">
              Quét QR shop để bắt đầu tích điểm.
            </p>
          </div>
        ) : (
          <section className="space-y-2">
            {entries?.map((entry: LedgerEntryResponse) => {
              const Icon = reasonIcon(entry.reason);
              return (
                <article
                  key={entry.id}
                  className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm"
                >
                  <div
                    className={
                      entry.delta > 0
                        ? "flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-brand-indigo"
                        : "flex h-12 w-12 items-center justify-center rounded-full bg-orange-50 text-brand-orange"
                    }
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-[14px] font-bold text-slate-800">
                      {reasonLabel(entry.reason)}
                    </h4>
                    {entry.description && (
                      <p className="text-[11px] text-slate-400">
                        {entry.description}
                      </p>
                    )}
                    <p className="text-[10px] text-slate-400">
                      {formatRelative(entry.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={
                        entry.delta >= 0
                          ? "font-headline text-[16px] font-bold text-brand-orange"
                          : "font-headline text-[16px] font-bold text-red-500"
                      }
                    >
                      {entry.delta >= 0 ? "+" : ""}
                      {entry.delta}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Còn {entry.balance_after}
                    </p>
                  </div>
                </article>
              );
            })}
          </section>
        )}
      </main>
    </>
  );
}
