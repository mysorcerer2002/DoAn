import { ArrowLeft, Crown, Search } from "lucide-react";
import Link from "next/link";

type Reward = {
  id: string;
  name: string;
  shop: string;
  emoji: string;
  bgColor: string;
  points: number;
  badge?: string;
  locked?: boolean;
  pointsNeeded?: number;
};

const rewards: Reward[] = [
  {
    id: "r1",
    name: "Cafe Latte size M Free",
    shop: "Cafe Cộng",
    emoji: "☕",
    bgColor: "bg-orange-50",
    points: 150,
    badge: "Còn 12",
  },
  {
    id: "r2",
    name: "Voucher 100K",
    shop: "Cafe Cộng",
    emoji: "🎫",
    bgColor: "bg-indigo-50",
    points: 500,
    badge: "Mới",
  },
  {
    id: "r3",
    name: "Bánh ngọt cao cấp",
    shop: "Cafe Cộng",
    emoji: "🎂",
    bgColor: "bg-pink-50",
    points: 200,
  },
  {
    id: "r4",
    name: "Combo trà sữa size L",
    shop: "Trà sữa Toko",
    emoji: "🥤",
    bgColor: "bg-violet-50",
    points: 250,
  },
  {
    id: "r5",
    name: "Bánh kem sinh nhật",
    shop: "Cafe Cộng",
    emoji: "🍰",
    bgColor: "bg-amber-50",
    points: 800,
  },
  {
    id: "r6",
    name: "Set quà cao cấp",
    shop: "Cocoon",
    emoji: "🎁",
    bgColor: "bg-pink-50",
    points: 2500,
    locked: true,
    pointsNeeded: 50,
  },
];

const filters = [
  { id: "all", label: "Tất cả", emoji: null },
  { id: "drink", label: "Đồ uống", emoji: "☕" },
  { id: "voucher", label: "Voucher", emoji: "🎫" },
  { id: "gift", label: "Quà tặng", emoji: "🎁" },
  { id: "exp", label: "Trải nghiệm", emoji: "✨" },
] as const;

export default function RewardsPage() {
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
          Đổi quà
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
          <div className="relative z-10 flex items-center justify-between">
            <div>
              <p className="text-[12px] font-medium text-indigo-100">
                Điểm hiện có
              </p>
              <div className="flex items-baseline gap-2">
                <span className="font-headline text-[32px] font-bold text-[#FB923C] leading-none">
                  2.450
                </span>
                <span className="text-[12px] text-indigo-100">điểm</span>
              </div>
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
              <Crown className="h-3.5 w-3.5 text-white" fill="white" />
              <span className="font-headline text-[12px] font-bold text-white">
                Hạng Vàng
              </span>
            </div>
          </div>
        </section>

        <section className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
          {filters.map((f, idx) => (
            <button
              key={f.id}
              type="button"
              className={
                idx === 0
                  ? "shrink-0 rounded-full bg-[#6366F1] px-4 py-1.5 text-[12px] font-bold text-white"
                  : "shrink-0 rounded-full border border-[#6366F1]/30 bg-white px-4 py-1.5 text-[12px] font-medium text-[#6366F1]"
              }
            >
              {f.emoji ? `${f.emoji} ${f.label}` : f.label}
            </button>
          ))}
        </section>

        <section className="space-y-3">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Đề xuất cho bạn
          </h2>
          <article className="relative flex items-center gap-4 overflow-hidden rounded-2xl bg-gradient-to-r from-[#FB923C] to-amber-400 p-4 shadow-lg">
            <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-xl bg-white/20 text-5xl backdrop-blur">
              🎁
            </div>
            <div className="flex-1 space-y-1">
              <span className="inline-block rounded-full bg-red-500 px-2 py-0.5 text-[9px] font-bold uppercase text-white">
                HOT
              </span>
              <h3 className="text-[16px] font-bold text-white">
                Voucher giảm 50.000đ
              </h3>
              <p className="text-[11px] text-white/90">
                Áp dụng cho hóa đơn từ 200.000đ
              </p>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[14px] font-bold text-white">
                  500 điểm
                </span>
                <button
                  type="button"
                  className="rounded-full bg-white px-3 py-1 text-[11px] font-bold text-[#FB923C]"
                >
                  Đổi ngay
                </button>
              </div>
            </div>
          </article>
        </section>

        <section className="grid grid-cols-2 gap-3 pb-4">
          {rewards.map((reward) => (
            <article
              key={reward.id}
              className={
                reward.locked
                  ? "relative overflow-hidden rounded-2xl border border-slate-100 bg-white opacity-60 shadow-sm"
                  : "relative overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm"
              }
            >
              {reward.badge && (
                <span className="absolute right-2 top-2 z-10 rounded-full bg-[#FB923C] px-2 py-0.5 text-[9px] font-bold text-white">
                  {reward.badge}
                </span>
              )}
              <div
                className={`flex aspect-square w-full items-center justify-center text-6xl ${reward.bgColor}`}
              >
                {reward.emoji}
              </div>
              <div className="space-y-1 p-3">
                <h4 className="font-headline text-[14px] font-bold leading-tight text-slate-800 line-clamp-2 min-h-[2.4rem]">
                  {reward.name}
                </h4>
                <p className="text-[11px] text-slate-400">{reward.shop}</p>
                <div className="flex items-center justify-between pt-1">
                  <span className="font-headline text-[14px] font-bold text-[#FB923C]">
                    {reward.points} điểm
                  </span>
                  {reward.locked ? (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500">
                      Cần thêm {reward.pointsNeeded}đ
                    </span>
                  ) : (
                    <button
                      type="button"
                      className="rounded-full bg-[#6366F1] px-3 py-1 text-[11px] font-bold text-white shadow-sm active:scale-95"
                    >
                      Đổi
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </section>
      </main>
    </>
  );
}
