"use client";

import {
  ArrowLeft,
  BookOpen,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Headphones,
  Info,
  MapPin,
  Share2,
  Sparkles,
  Store,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
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

function formatVnd(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString("vi-VN") + "₫";
}

function daysLeft(iso: string): number {
  const diff = new Date(iso).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function discountLabel(v: VoucherResponse): string {
  if (!v.discount_value) return "—";
  return v.discount_type === "percent"
    ? `Giảm ${v.discount_value}%`
    : `Giảm ${formatVnd(v.discount_value)}`;
}

function parseLines(text: string | null | undefined): string[] {
  if (!text) return [];
  return text
    .split(/\r?\n/)
    .map((l) => l.replace(/^[•\-\d.\s)]+/, "").trim())
    .filter(Boolean);
}

const STATUS_META: Record<
  string,
  { label: string; bg: string; text: string }
> = {
  issued: {
    label: "Còn hiệu lực",
    bg: "bg-emerald-50",
    text: "text-emerald-700",
  },
  used: { label: "Đã sử dụng", bg: "bg-slate-100", text: "text-slate-600" },
  expired: { label: "Hết hạn", bg: "bg-red-50", text: "text-red-600" },
};

export default function VoucherDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const voucherId = Number(params.id);
  const { data: vouchers, isLoading, isError } = useMyVouchers();
  const [copied, setCopied] = useState(false);

  const voucher = useMemo(
    () => vouchers?.find((v: VoucherResponse) => v.id === voucherId) ?? null,
    [vouchers, voucherId]
  );

  const handleCopy = async () => {
    if (!voucher) return;
    try {
      await navigator.clipboard.writeText(voucher.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-orange/30 border-t-brand-orange" />
      </div>
    );
  }

  if (isError || !voucher) {
    return (
      <div className="px-4 pt-12">
        <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-10 text-center">
          <p className="font-headline text-[16px] font-bold text-slate-700">
            Không tìm thấy voucher
          </p>
          <p className="mt-1 text-[12px] text-slate-500">
            Voucher có thể đã bị xoá hoặc không thuộc về bạn.
          </p>
          <Link
            href="/member/vouchers"
            className="mt-4 inline-flex items-center gap-1 rounded-full bg-brand-indigo px-4 py-2 text-[12px] font-bold text-white"
          >
            <ArrowLeft className="h-4 w-4" /> Về danh sách voucher
          </Link>
        </div>
      </div>
    );
  }

  const status = STATUS_META[voucher.status] ?? STATUS_META.issued;
  const days = daysLeft(voucher.expires_at);
  const isExpired = voucher.status === "expired" || days === 0;
  const isUsed = voucher.status === "used";
  const terms = parseLines(voucher.campaign_terms);
  const guide = parseLines(voucher.campaign_usage_guide);

  return (
    <>
      {/* Sticky header */}
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between bg-white/95 px-4 backdrop-blur shadow-sm">
        <button
          type="button"
          onClick={() => router.back()}
          className="flex h-10 w-10 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-6 w-6" />
        </button>
        <h1 className="font-headline text-[16px] font-bold text-slate-800">
          Chi tiết voucher
        </h1>
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100"
          aria-label="Chia sẻ"
        >
          <Share2 className="h-5 w-5" />
        </button>
      </header>

      <main className="space-y-4 px-4 pb-32 pt-4">
        {/* Hero ticket card */}
        <section className="relative">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-orange via-orange-500 to-orange-600 p-6 shadow-2xl shadow-orange-300/50">
            {/* Decorative blobs */}
            <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-white/10 blur-3xl" />
            <div className="pointer-events-none absolute -left-12 bottom-0 h-32 w-32 rounded-full bg-amber-300/20 blur-2xl" />

            {/* Top section: badge + title + amount */}
            <div className="relative z-10">
              <div className="flex items-start justify-between gap-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-white backdrop-blur">
                  <Sparkles className="h-3 w-3" />
                  Voucher
                </span>
                <span
                  className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${status.bg} ${status.text}`}
                >
                  {status.label}
                </span>
              </div>

              <h2 className="mt-4 font-headline text-[24px] font-bold leading-tight text-white">
                {voucher.campaign_name ?? `Voucher ${voucher.code}`}
              </h2>
              <p className="mt-1 text-[14px] font-bold text-white/90">
                {discountLabel(voucher)}
                {voucher.discount_type === "percent" &&
                  voucher.max_discount != null && (
                    <span className="ml-1 font-normal text-white/75">
                      · tối đa {formatVnd(voucher.max_discount)}
                    </span>
                  )}
              </p>
            </div>

            {/* Notch dividers */}
            <div className="relative z-10 my-4 flex items-center">
              <div className="absolute -left-9 h-5 w-5 rounded-full bg-[#f8fafc]" />
              <div className="absolute -right-9 h-5 w-5 rounded-full bg-[#f8fafc]" />
              <div className="flex-1 border-t-2 border-dashed border-white/40" />
            </div>

            {/* Bottom info grid */}
            <div className="relative z-10 grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-white/70">
                  Đơn tối thiểu
                </p>
                <p className="mt-0.5 font-headline text-[15px] font-bold text-white">
                  {voucher.min_order != null && voucher.min_order > 0
                    ? formatVnd(voucher.min_order)
                    : "Không giới hạn"}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-white/70">
                  Hạn sử dụng
                </p>
                <p className="mt-0.5 font-headline text-[15px] font-bold text-white">
                  {formatDate(voucher.expires_at)}
                </p>
              </div>
            </div>
          </div>

          {/* Floating days-left chip */}
          {!isUsed && !isExpired && (
            <div className="absolute -bottom-3 left-1/2 z-20 -translate-x-1/2 rounded-full bg-white px-4 py-1.5 shadow-lg shadow-orange-200">
              <span className="flex items-center gap-1 text-[11px] font-bold text-brand-orange">
                <Clock className="h-3.5 w-3.5" />
                Còn {days} ngày
              </span>
            </div>
          )}
        </section>

        {/* QR code for staff to scan */}
        {!isUsed && !isExpired && (
          <section className="rounded-2xl bg-white p-5 shadow-sm">
            <div className="flex items-center justify-center">
              <div className="rounded-2xl border-2 border-dashed border-brand-orange/40 bg-orange-50/40 p-4">
                <QRCodeSVG
                  value={voucher.code}
                  size={200}
                  level="H"
                  bgColor="#ffffff"
                  fgColor="#0f172a"
                  marginSize={2}
                />
              </div>
            </div>
            <p className="mt-4 text-center font-mono text-[20px] font-bold tracking-[0.2em] text-slate-800">
              {voucher.code}
            </p>
            <p className="mt-2 text-center text-[12px] leading-relaxed text-slate-500">
              Đưa mã QR này cho nhân viên quét tại quầy thanh toán
              <br />
              hoặc đọc dãy mã ở trên cho nhân viên nhập tay
            </p>
            <button
              type="button"
              onClick={handleCopy}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-brand-orange/30 bg-orange-50 py-2.5 text-[12px] font-bold text-brand-orange transition active:scale-[0.99]"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4" /> Đã sao chép
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" /> Sao chép mã voucher
                </>
              )}
            </button>
          </section>
        )}

        {/* Description */}
        {voucher.campaign_description && (
          <SectionCard
            icon={<Info className="h-5 w-5 text-brand-orange" />}
            iconBg="bg-orange-100"
            title="Mô tả ưu đãi"
          >
            <p className="text-[13px] leading-relaxed text-slate-600">
              {voucher.campaign_description}
            </p>
          </SectionCard>
        )}

        {/* Terms */}
        {terms.length > 0 && (
          <SectionCard
            icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
            iconBg="bg-emerald-50"
            title="Điều kiện áp dụng"
          >
            <ul className="space-y-2.5">
              {terms.map((t, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-100">
                    <Check className="h-3 w-3 text-emerald-600" strokeWidth={3} />
                  </span>
                  <span className="text-[13px] leading-relaxed text-slate-600">
                    {t}
                  </span>
                </li>
              ))}
            </ul>
          </SectionCard>
        )}

        {/* Usage guide */}
        {guide.length > 0 && (
          <SectionCard
            icon={<BookOpen className="h-5 w-5 text-brand-indigo" />}
            iconBg="bg-indigo-50"
            title="Hướng dẫn sử dụng"
          >
            <ol className="space-y-3">
              {guide.map((step, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-indigo/10 font-headline text-[12px] font-bold text-brand-indigo">
                    {i + 1}
                  </span>
                  <span className="text-[13px] leading-relaxed text-slate-600">
                    {step}
                  </span>
                </li>
              ))}
            </ol>
          </SectionCard>
        )}

        {/* Support */}
        {voucher.campaign_support_contact && (
          <SectionCard
            icon={<Headphones className="h-5 w-5 text-brand-violet" />}
            iconBg="bg-violet-50"
            title="Liên hệ hỗ trợ"
          >
            <p className="whitespace-pre-line text-[13px] leading-relaxed text-slate-600">
              {voucher.campaign_support_contact}
            </p>
          </SectionCard>
        )}

        {/* Used at */}
        {isUsed && voucher.used_at && (
          <div className="rounded-2xl bg-slate-100 p-4 text-center">
            <p className="text-[12px] text-slate-600">
              Đã sử dụng vào{" "}
              <span className="font-bold text-slate-800">
                {formatDate(voucher.used_at)}
              </span>
            </p>
          </div>
        )}
      </main>

      {/* Bottom action bar */}
      {!isUsed && !isExpired && (
        <div className="fixed inset-x-0 bottom-0 z-40 mx-auto max-w-md border-t border-slate-100 bg-white/95 px-4 py-3 backdrop-blur">
          <div className="flex gap-3">
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 rounded-2xl border-2 border-brand-indigo bg-white py-3 font-headline text-[13px] font-bold text-brand-indigo transition active:scale-[0.98]"
            >
              <Store className="h-4 w-4" />
              Dùng tại shop
            </button>
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3 font-headline text-[13px] font-bold text-white shadow-lg shadow-indigo-200 transition active:scale-[0.98]"
            >
              <MapPin className="h-4 w-4" />
              Đường đi
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function SectionCard({
  icon,
  iconBg,
  title,
  children,
}: {
  icon: React.ReactNode;
  iconBg: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-full ${iconBg}`}
        >
          {icon}
        </span>
        <h3 className="font-headline text-[14px] font-bold text-slate-800">
          {title}
        </h3>
      </div>
      <div className="mt-3">{children}</div>
    </section>
  );
}
