"use client";

import { ArrowLeft, Gift, Loader2, Tag } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  useMyRedemptions,
  type MyRedemptionListItem,
} from "@/lib/hooks/useRedemptions";

type TabStatus = "pending" | "used" | "expired";

const TAB_LABELS: Record<TabStatus, string> = {
  pending: "Chưa dùng",
  used: "Đã dùng",
  expired: "Hết hạn",
};

const STATUS_BADGE: Record<TabStatus, string> = {
  pending: "bg-emerald-100 text-emerald-700",
  used: "bg-slate-100 text-slate-500",
  expired: "bg-red-50 text-red-500",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function RedemptionCard({ item }: { item: MyRedemptionListItem }) {
  const status = item.status as TabStatus;
  return (
    <Link href={`/member/vouchers/${item.id}`}>
      <article className="flex gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm active:scale-[0.99] transition-transform">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-3xl">
          <Gift className="h-7 w-7 text-brand-indigo" />
        </div>
        <div className="min-w-0 flex-1 space-y-1">
          <h3 className="truncate font-headline text-[14px] font-bold text-slate-800">
            {item.reward_name}
          </h3>
          <p className="truncate text-[12px] text-slate-400">
            {item.partner_name}
          </p>
          <div className="flex items-center justify-between pt-0.5">
            <span className="font-mono text-[11px] font-bold tracking-widest text-brand-indigo">
              {item.redemption_code}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-bold",
                STATUS_BADGE[status]
              )}
            >
              {TAB_LABELS[status]}
            </span>
          </div>
          {status === "pending" && (
            <p className="text-[11px] text-slate-400">
              Hết hạn: {formatDate(item.expires_at)}
            </p>
          )}
        </div>
      </article>
    </Link>
  );
}

export default function VouchersPage() {
  const [activeTab, setActiveTab] = useState<TabStatus>("pending");
  const { data, isLoading, isError } = useMyRedemptions(activeTab);

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
          Ví Voucher
        </h1>
        <div className="w-10" />
      </header>

      {/* Tabs */}
      <div className="flex border-b border-slate-100 bg-white px-4">
        {(Object.keys(TAB_LABELS) as TabStatus[]).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={cn(
              "flex-1 py-3 text-[13px] font-medium transition-colors",
              activeTab === tab
                ? "border-b-2 border-brand-indigo font-bold text-brand-indigo"
                : "text-slate-400"
            )}
          >
            {TAB_LABELS[tab]}
          </button>
        ))}
      </div>

      <main className="space-y-3 px-4 py-4 pb-8">
        {isLoading ? (
          <div className="flex min-h-[40vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-[13px] text-red-600">
            Không tải được danh sách voucher
          </div>
        ) : (data?.items ?? []).length === 0 ? (
          <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
            <Tag className="h-12 w-12 text-slate-300" />
            <p className="font-bold text-slate-600">
              {activeTab === "pending"
                ? "Chưa có voucher nào"
                : activeTab === "used"
                  ? "Chưa dùng voucher nào"
                  : "Không có voucher hết hạn"}
            </p>
            {activeTab === "pending" && (
              <Link
                href="/member/rewards"
                className="text-[13px] font-bold text-brand-indigo hover:underline"
              >
                Đổi quà ngay →
              </Link>
            )}
          </div>
        ) : (
          (data?.items ?? []).map((item) => (
            <RedemptionCard key={item.id} item={item} />
          ))
        )}
      </main>
    </>
  );
}
