import {
  Bell,
  Crown,
  QrCode,
  Gift,
  Ticket,
  History,
  Clock,
} from "lucide-react";

const favoriteShops = [
  {
    id: 1,
    name: "Cafe Cộng Bà Triệu",
    address: "Hai Bà Trưng, HN",
    emoji: "☕",
    tier: "Hạng Bạc",
    tierTone: "slate",
    points: 320,
  },
  {
    id: 2,
    name: "Phở Thìn Lò Đúc",
    address: "Hai Bà Trưng, HN",
    emoji: "🍜",
    tier: "Hạng Đồng",
    tierTone: "slate",
    points: 150,
  },
  {
    id: 3,
    name: "Coolmate Pop-up",
    address: "Hoàn Kiếm, HN",
    emoji: "🛍️",
    tier: "Hạng Vàng",
    tierTone: "indigo",
    points: 890,
  },
] as const;

const availableVouchers = [
  {
    id: 1,
    title: "Giảm 20% Coffee",
    description: "Áp dụng cho mọi món",
    expiry: "20/04/2026",
    valueLabel: "20%",
  },
  {
    id: 2,
    title: "Free Upsize",
    description: "Cho trà trái cây size L",
    expiry: "15/05/2026",
    valueLabel: "0đ",
  },
] as const;

const quickActions = [
  { id: "qr", icon: QrCode, label: "Mã QR", color: "indigo" },
  { id: "redeem", icon: Gift, label: "Đổi quà", color: "orange" },
  { id: "voucher", icon: Ticket, label: "Voucher", color: "orange" },
  { id: "history", icon: History, label: "Lịch sử", color: "indigo" },
] as const;

export default function MemberDashboardPage() {
  return (
    <>
      {/* TopAppBar */}
      <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between bg-slate-50/95 px-4 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 overflow-hidden rounded-full border-2 border-indigo-100 bg-gradient-to-br from-indigo-200 to-violet-200">
            <div className="flex h-full w-full items-center justify-center text-lg font-bold text-indigo-700">
              MA
            </div>
          </div>
          <h1 className="font-headline text-[16px] font-bold text-slate-800">
            Chào, Minh Anh ☀️
          </h1>
        </div>
        <button
          type="button"
          className="group relative cursor-pointer transition-opacity hover:opacity-80"
          aria-label="Thông báo"
        >
          <Bell className="h-6 w-6 text-indigo-600" />
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full border-2 border-slate-50 bg-red-500 text-[10px] font-bold text-white">
            3
          </span>
        </button>
      </header>

      <main className="space-y-6 px-4 pt-2">
        {/* Hero Points Card */}
        <section className="relative overflow-hidden rounded-[20px] bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] p-6 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 space-y-4">
            <div className="flex items-start justify-between">
              <p className="font-headline text-[12px] font-extrabold uppercase tracking-widest text-indigo-100/80">
                TỔNG ĐIỂM TÍCH LŨY
              </p>
              <div className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
                <Crown className="h-3.5 w-3.5 text-white" fill="white" />
                <span className="font-headline text-[12px] font-bold text-white">
                  Hạng Vàng
                </span>
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-headline text-glow-orange text-[64px] font-bold leading-none text-[#FB923C]">
                2.450
              </span>
              <span className="font-medium text-indigo-100">điểm</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[12px] font-medium text-indigo-50">
                <span>Còn 550 điểm để lên Bạch Kim</span>
                <span>80%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-white/20">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#FB923C] to-orange-300"
                  style={{ width: "80%" }}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Quick Actions */}
        <section className="grid grid-cols-4 gap-3">
          {quickActions.map(({ id, icon: Icon, label, color }) => (
            <button
              key={id}
              type="button"
              className="group flex flex-col items-center gap-2"
            >
              <div className="flex aspect-square w-full items-center justify-center rounded-2xl border border-slate-100 bg-white shadow-sm transition-transform group-active:scale-95">
                <Icon
                  className={
                    color === "indigo"
                      ? "h-6 w-6 text-indigo-600"
                      : "h-6 w-6 text-[#FB923C]"
                  }
                />
              </div>
              <span className="text-[11px] font-medium text-slate-600">
                {label}
              </span>
            </button>
          ))}
        </section>

        {/* Favorite Stores */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-headline text-[18px] font-bold text-slate-800">
              Cửa hàng yêu thích
            </h3>
            <a
              href="#"
              className="text-[14px] font-semibold text-indigo-600 hover:underline"
            >
              Xem tất cả
            </a>
          </div>
          <div className="no-scrollbar -mx-4 flex gap-4 overflow-x-auto px-4 pb-4">
            {favoriteShops.map((shop) => (
              <div
                key={shop.id}
                className="min-w-[180px] shrink-0 space-y-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-2xl shadow-inner">
                  {shop.emoji}
                </div>
                <div className="space-y-1">
                  <h4 className="truncate text-[14px] font-bold text-slate-800">
                    {shop.name}
                  </h4>
                  <p className="truncate text-[12px] text-slate-400">
                    {shop.address}
                  </p>
                </div>
                <div className="flex items-center justify-between border-t border-slate-50 pt-2">
                  <span
                    className={
                      shop.tierTone === "indigo"
                        ? "rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold uppercase text-indigo-500"
                        : "rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-500"
                    }
                  >
                    {shop.tier}
                  </span>
                  <span className="text-[14px] font-bold text-[#FB923C]">
                    {shop.points} đ
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Available Vouchers */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <h3 className="font-headline text-[18px] font-bold text-slate-800">
              Voucher khả dụng
            </h3>
            <span className="rounded-full bg-[#FB923C]/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#FB923C]">
              2 voucher mới
            </span>
          </div>
          <div className="space-y-4">
            {availableVouchers.map((voucher) => (
              <article
                key={voucher.id}
                className="relative flex items-center overflow-hidden rounded-2xl border-l-4 border-[#FB923C] bg-white shadow-sm"
              >
                <span className="absolute -top-1 left-24 h-4 w-4 rounded-full border border-slate-100 bg-[#f8fafc]" />
                <span className="absolute -bottom-1 left-24 h-4 w-4 rounded-full border border-slate-100 bg-[#f8fafc]" />
                <div className="flex-1 p-4">
                  <h4 className="text-[16px] font-bold text-slate-800">
                    {voucher.title}
                  </h4>
                  <p className="text-[12px] text-slate-500">
                    {voucher.description}
                  </p>
                  <p className="mt-2 flex items-center gap-1 text-[11px] text-slate-400">
                    <Clock className="h-3.5 w-3.5" />
                    Hết hạn {voucher.expiry}
                  </p>
                </div>
                <div className="flex min-w-[100px] flex-col items-center justify-center border-l border-dashed border-slate-200 bg-slate-50/50 p-4">
                  <span className="text-[28px] font-bold text-[#FB923C]">
                    {voucher.valueLabel}
                  </span>
                  <button
                    type="button"
                    className="mt-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-[11px] font-bold text-white transition-colors hover:bg-indigo-700"
                  >
                    Áp dụng
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
