"use client";

import {
  ArrowRight,
  Building2,
  CreditCard,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

import { useMe } from "@/lib/hooks/use-me";
import { usePartnerStore } from "@/lib/partner-store";

export default function StaffDashboardPage() {
  const { data: user } = useMe();
  const partner = usePartnerStore((s) => s.activePartner);

  const firstName = (() => {
    const full = user?.full_name?.trim() ?? "";
    if (!full) return "bạn";
    const parts = full.split(/\s+/);
    return parts[parts.length - 1];
  })();

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Cửa hàng / Tổng quan</p>
        <h1 className="mt-1 font-headline text-[28px] font-bold text-slate-800 md:text-[32px]">
          Chào {firstName} 👋
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Sẵn sàng phục vụ khách hàng tại {partner?.name ?? "cửa hàng"}
        </p>
      </header>

      {/* Hero CTA tạo giao dịch */}
      <section className="mt-6 overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-700 via-emerald-800 to-emerald-900 p-6 text-white shadow-xl shadow-emerald-200 md:p-8">
        <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div className="relative z-10 flex flex-col items-start gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex-1">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold uppercase tracking-widest backdrop-blur">
              <Sparkles className="h-3 w-3 text-brand-orange" />
              Hành động chính
            </div>
            <h2 className="mt-4 font-headline text-[28px] font-bold leading-tight md:text-[36px]">
              Tạo giao dịch tích điểm
            </h2>
            <p className="mt-2 max-w-md text-[14px] text-emerald-100">
              Quét QR khách hoặc nhập SĐT, áp voucher (nếu có), tự động cộng
              điểm + cập nhật hạng thành viên.
            </p>
            <Link
              href="/staff/pos/transactions/new"
              className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-white px-6 py-4 font-headline text-[14px] font-bold text-emerald-700 shadow-xl transition-transform hover:scale-[1.02]"
            >
              Bắt đầu tạo giao dịch
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
          <div className="hidden h-24 w-24 items-center justify-center rounded-3xl bg-white/15 backdrop-blur md:flex">
            <CreditCard className="h-12 w-12 text-white" />
          </div>
        </div>
      </section>

      {/* Info shop card */}
      <section className="mt-6 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
            <Building2 className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <h3 className="font-headline text-[16px] font-bold text-slate-800">
              {partner?.name ?? "Cửa hàng"}
            </h3>
            <p className="mt-1 font-mono text-[11px] text-slate-400">
              slug: {partner?.slug}
            </p>
            <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-700">
              Vai trò: Nhân viên
            </div>
          </div>
        </div>
      </section>

      {/* Hướng dẫn nhanh */}
      <section className="mt-6 rounded-2xl border border-amber-100 bg-amber-50 p-5">
        <h3 className="font-headline text-[14px] font-bold text-amber-800">
          💡 Hướng dẫn nhanh
        </h3>
        <ol className="mt-3 space-y-2 text-[13px] text-amber-900">
          <li>
            <strong>1.</strong> Bấm "Tạo giao dịch" → nhập SĐT khách hoặc quét
            QR.
          </li>
          <li>
            <strong>2.</strong> Nhập tổng tiền hoá đơn (gross_amount).
          </li>
          <li>
            <strong>3.</strong> Nếu khách có voucher: nhập mã → hệ thống tự áp
            dụng giảm giá.
          </li>
          <li>
            <strong>4.</strong> Bấm xác nhận → khách nhận điểm tự động.
          </li>
        </ol>
      </section>
    </main>
  );
}
