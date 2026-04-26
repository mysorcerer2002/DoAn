"use client";

import { ArrowLeft, Loader2, Store } from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { QRCodeSVG } from "qrcode.react";
import { cn } from "@/lib/utils";
import { useMyRedemption } from "@/lib/hooks/useRedemptions";

type TabStatus = "pending" | "used" | "expired";

const STATUS_LABEL: Record<TabStatus, string> = {
  pending: "Chưa dùng",
  used: "Đã dùng",
  expired: "Hết hạn",
};

const STATUS_COLOR: Record<TabStatus, string> = {
  pending: "bg-emerald-100 text-emerald-700",
  used: "bg-slate-100 text-slate-500",
  expired: "bg-red-50 text-red-500",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function VoucherDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const redemptionId = Number(id);
  const { data, isLoading, isError } = useMyRedemption(redemptionId);

  return (
    <>
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between bg-slate-50/95 px-4 backdrop-blur">
        <Link
          href="/member/vouchers"
          className="flex h-10 w-10 items-center justify-center rounded-full text-brand-indigo hover:bg-indigo-50"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <h1 className="font-headline text-[18px] font-bold text-slate-800">
          Chi tiết voucher
        </h1>
        <div className="w-10" />
      </header>

      <main className="space-y-4 px-4 py-4 pb-8">
        {isLoading ? (
          <div className="flex min-h-[60vh] items-center justify-center">
            <Loader2 className="h-10 w-10 animate-spin text-brand-indigo" />
          </div>
        ) : isError || !data ? (
          <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
            <p className="font-bold text-slate-600">Không tìm thấy voucher</p>
            <Link
              href="/member/vouchers"
              className="text-[13px] font-bold text-brand-indigo hover:underline"
            >
              Quay lại ví voucher
            </Link>
          </div>
        ) : (
          <>
            {/* QR card */}
            <section className="flex flex-col items-center gap-4 rounded-3xl border border-slate-100 bg-white p-6 shadow-md">
              <div
                className={cn(
                  "rounded-full px-4 py-1 text-[12px] font-bold",
                  STATUS_COLOR[data.status as TabStatus]
                )}
              >
                {STATUS_LABEL[data.status as TabStatus]}
              </div>

              <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 shadow-inner">
                <QRCodeSVG
                  value={data.redemption_code}
                  size={200}
                  bgColor="#f8fafc"
                  fgColor="#1e1b4b"
                  level="M"
                />
              </div>

              <div className="text-center">
                <p className="font-mono text-[24px] font-bold tracking-[0.25em] text-brand-indigo">
                  {data.redemption_code}
                </p>
                <p className="mt-1 text-[11px] text-slate-400">
                  Xuất trình mã này tại quầy
                </p>
              </div>
            </section>

            {/* Reward info */}
            <section className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
              <h2 className="font-headline text-[16px] font-bold text-slate-800">
                {data.reward_name}
              </h2>
              <div className="mt-2 flex items-center gap-2 text-[12px] text-slate-500">
                <Store className="h-3.5 w-3.5" />
                <span>{data.partner_name}</span>
              </div>
              {data.reward_description && (
                <p className="mt-3 text-[13px] leading-relaxed text-slate-600">
                  {data.reward_description}
                </p>
              )}
            </section>

            {/* Details */}
            <section className="rounded-2xl border border-slate-100 bg-white divide-y divide-slate-50 shadow-sm">
              <InfoRow label="Điểm đã dùng" value={`${data.points_spent.toLocaleString("vi-VN")} điểm`} />
              <InfoRow label="Ngày đổi" value={formatDate(data.redeemed_at)} />
              <InfoRow label="Hết hạn" value={formatDate(data.expires_at)} />
              {data.used_at && (
                <InfoRow label="Đã dùng lúc" value={formatDate(data.used_at)} />
              )}
            </section>

            {/* Terms */}
            {data.reward_terms && (
              <section className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                <h3 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-400">
                  Điều kiện áp dụng
                </h3>
                <p className="text-[12px] leading-relaxed text-slate-500">
                  {data.reward_terms}
                </p>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <span className="text-[12px] text-slate-400">{label}</span>
      <span className="text-[13px] font-medium text-slate-700">{value}</span>
    </div>
  );
}
