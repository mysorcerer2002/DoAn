import { ArrowLeft, Clock, Coffee, Gift, Plus, Search, Ticket } from "lucide-react";
import Link from "next/link";

type Voucher = {
  id: string;
  title: string;
  description: string;
  shop: string;
  expiry: string;
  daysLeft: number;
  valueLabel: string;
  icon: "ticket" | "coffee" | "gift";
  badge?: string;
  variant?: "default" | "premium";
};

const vouchers: Voucher[] = [
  {
    id: "v1",
    title: "Giảm 50.000₫",
    description: "Áp dụng cho hóa đơn từ 200K",
    shop: "Cafe Cộng - Bà Triệu",
    expiry: "20/04/2026",
    daysLeft: 5,
    valueLabel: "50K",
    icon: "ticket",
    badge: "MỚI",
  },
  {
    id: "v2",
    title: "Free Cafe Latte size M",
    description: "Áp dụng mọi món Latte",
    shop: "Cafe Cộng",
    expiry: "27/04/2026",
    daysLeft: 12,
    valueLabel: "Free",
    icon: "coffee",
  },
  {
    id: "v3",
    title: "Giảm 20%",
    description: "Toàn bộ menu",
    shop: "Trà sữa Toko",
    expiry: "13/05/2026",
    daysLeft: 30,
    valueLabel: "20%",
    icon: "ticket",
    variant: "premium",
  },
  {
    id: "v4",
    title: "Quà sinh nhật: Bánh ngọt",
    description: "Miễn phí khi check-in",
    shop: "BBQ Hàn Quốc",
    expiry: "20/04/2026",
    daysLeft: 7,
    valueLabel: "Free",
    icon: "gift",
  },
];

const tabs = [
  { id: "available", label: "Khả dụng (12)" },
  { id: "used", label: "Đã dùng (5)" },
  { id: "expired", label: "Hết hạn (3)" },
] as const;

export default function VouchersPage() {
  return (
    <>
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between bg-slate-50/95 px-4 backdrop-blur">
        <Link
          href="/member"
          className="flex h-10 w-10 items-center justify-center rounded-full text-[#6366F1] hover:bg-indigo-50"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <h1 className="font-headline text-[18px] font-bold text-slate-800">
          Voucher của tôi
        </h1>
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-[#6366F1] hover:bg-indigo-50"
          aria-label="Tìm kiếm"
        >
          <Search className="h-6 w-6" />
        </button>
      </header>

      <main className="space-y-4 px-4 pt-2">
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] p-4 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 space-y-1">
            <p className="text-[14px] font-bold text-white">
              Bạn có 12 voucher khả dụng
            </p>
            <p className="text-[12px] font-bold text-[#FB923C]">
              Tiết kiệm tới 850.000₫
            </p>
          </div>
        </section>

        <section className="flex items-center gap-2 overflow-x-auto pb-1">
          {tabs.map((tab, idx) => (
            <button
              key={tab.id}
              type="button"
              className={
                idx === 0
                  ? "shrink-0 rounded-full bg-[#6366F1]/10 px-4 py-2 text-[12px] font-bold text-[#6366F1]"
                  : "shrink-0 rounded-full border border-slate-200 bg-white px-4 py-2 text-[12px] font-medium text-slate-500"
              }
            >
              {tab.label}
            </button>
          ))}
        </section>

        <div className="space-y-3 pb-8">
          {vouchers.map((voucher) =>
            voucher.variant === "premium" ? (
              <PremiumVoucher key={voucher.id} voucher={voucher} />
            ) : (
              <StandardVoucher key={voucher.id} voucher={voucher} />
            )
          )}
        </div>
      </main>

      {/* Floating action button */}
      <button
        type="button"
        className="fixed bottom-28 right-4 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-tr from-[#6366F1] to-[#8B5CF6] text-white shadow-xl shadow-indigo-300 active:scale-95"
        aria-label="Khám phá chiến dịch"
      >
        <Plus className="h-7 w-7" />
      </button>
    </>
  );
}

function StandardVoucher({ voucher }: { voucher: Voucher }) {
  const Icon =
    voucher.icon === "coffee" ? Coffee : voucher.icon === "gift" ? Gift : Ticket;
  return (
    <article className="relative flex items-stretch overflow-hidden rounded-2xl border-l-4 border-[#FB923C] bg-white shadow-sm">
      {voucher.badge && (
        <span className="absolute right-2 top-2 z-10 rounded-full bg-[#FB923C] px-2 py-0.5 text-[9px] font-bold uppercase text-white">
          {voucher.badge}
        </span>
      )}
      {/* Notch top + bottom */}
      <span className="absolute -top-1 left-[100px] h-3 w-3 rounded-full border border-slate-100 bg-[#f8fafc]" />
      <span className="absolute -bottom-1 left-[100px] h-3 w-3 rounded-full border border-slate-100 bg-[#f8fafc]" />

      <div className="flex w-[100px] shrink-0 items-center justify-center bg-orange-50">
        <Icon className="h-9 w-9 text-[#FB923C]" />
      </div>

      <div className="flex-1 p-4">
        <h3 className="font-headline text-[16px] font-bold text-slate-800">
          {voucher.title}
        </h3>
        <p className="text-[12px] text-slate-500">{voucher.description}</p>
        <p className="mt-1 text-[11px] font-medium text-[#6366F1]">
          {voucher.shop}
        </p>
        <div className="mt-2 flex items-center justify-between">
          <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
            <Clock className="h-3 w-3" />
            Còn {voucher.daysLeft} ngày
          </span>
          <button
            type="button"
            className="rounded-full bg-[#6366F1] px-3 py-1 text-[11px] font-bold text-white shadow-sm active:scale-95"
          >
            Dùng ngay
          </button>
        </div>
      </div>
    </article>
  );
}

function PremiumVoucher({ voucher }: { voucher: Voucher }) {
  return (
    <article className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#FB923C] to-amber-500 p-4 shadow-lg">
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-white/10 blur-xl" />
      <div className="relative z-10 flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="font-headline text-[26px] font-bold text-white">
            {voucher.title}
          </h3>
          <p className="text-[13px] text-white/90">{voucher.description}</p>
          <p className="text-[11px] font-medium text-white/80">
            {voucher.shop}
          </p>
          <div className="flex items-center gap-1 pt-1 text-[11px] text-white">
            <Clock className="h-3 w-3" />
            Còn {voucher.daysLeft} ngày
          </div>
        </div>
        <button
          type="button"
          className="rounded-full bg-white px-4 py-2 text-[12px] font-bold text-[#FB923C] shadow active:scale-95"
        >
          Dùng
        </button>
      </div>
    </article>
  );
}
