import { ArrowLeft, ChevronRight, Filter } from "lucide-react";
import Link from "next/link";

type Transaction = {
  id: string;
  type: "earn" | "redeem" | "bonus";
  title: string;
  shop: string;
  amount?: string;
  points: number;
  time: string;
  emoji: string;
};

type DayGroup = { label: string; items: Transaction[] };

const groups: DayGroup[] = [
  {
    label: "Hôm nay - 13/04/2026",
    items: [
      {
        id: "tx-1",
        type: "earn",
        title: "Tích điểm tại Cafe Cộng",
        shop: "Cafe Cộng - Bà Triệu",
        amount: "150.000 ₫",
        points: 15,
        time: "14:30",
        emoji: "☕",
      },
      {
        id: "tx-2",
        type: "redeem",
        title: "Đổi voucher giảm 50K",
        shop: "Cafe Cộng - Bà Triệu",
        points: -300,
        time: "10:15",
        emoji: "🎁",
      },
    ],
  },
  {
    label: "Hôm qua - 12/04/2026",
    items: [
      {
        id: "tx-3",
        type: "earn",
        title: "Tích điểm Trà sữa Toko",
        shop: "Trà sữa Toko",
        amount: "80.000 ₫",
        points: 8,
        time: "18:20",
        emoji: "🥤",
      },
      {
        id: "tx-4",
        type: "earn",
        title: "Tích điểm BBQ Hàn",
        shop: "BBQ Hàn Quốc",
        amount: "250.000 ₫",
        points: 25,
        time: "19:45",
        emoji: "🍜",
      },
      {
        id: "tx-5",
        type: "bonus",
        title: "Bonus chiến dịch x2 điểm",
        shop: "Welcome",
        points: 50,
        time: "09:00",
        emoji: "✨",
      },
    ],
  },
  {
    label: "Tuần trước - 04-11/04",
    items: [
      {
        id: "tx-6",
        type: "earn",
        title: "Tích điểm Pizza Hut",
        shop: "Pizza Hut Hoàn Kiếm",
        amount: "320.000 ₫",
        points: 32,
        time: "11/04 19:00",
        emoji: "🍕",
      },
      {
        id: "tx-7",
        type: "earn",
        title: "Tích điểm Coolmate",
        shop: "Coolmate Pop-up",
        amount: "450.000 ₫",
        points: 45,
        time: "08/04 15:30",
        emoji: "🛍️",
      },
    ],
  },
];

const filterTabs = [
  { id: "all", label: "Tất cả" },
  { id: "earn", label: "Tích điểm" },
  { id: "redeem", label: "Đổi quà" },
  { id: "voucher", label: "Voucher" },
] as const;

export default function HistoryPage() {
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
              Tổng điểm tích lũy 30 ngày qua
            </p>
            <p className="font-headline text-[36px] font-bold text-brand-orange text-glow-orange leading-none">
              +450 điểm
            </p>
            <p className="text-[12px] text-indigo-50/80">
              Từ 12 giao dịch tại 3 cửa hàng
            </p>
            <div className="flex gap-3 pt-2">
              <span className="rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold text-white">
                12 GD
              </span>
              <span className="rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold text-white">
                1.840.000 ₫ chi tiêu
              </span>
            </div>
          </div>
        </section>

        <section className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
          {filterTabs.map((tab, idx) => (
            <button
              key={tab.id}
              type="button"
              className={
                idx === 0
                  ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                  : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
              }
            >
              {tab.label}
            </button>
          ))}
        </section>

        {groups.map((group) => (
          <section key={group.label} className="space-y-3">
            <div className="rounded-lg bg-slate-100 px-3 py-1.5">
              <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">
                {group.label}
              </p>
            </div>
            <div className="space-y-2">
              {group.items.map((tx) => (
                <article
                  key={tx.id}
                  className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm"
                >
                  <div
                    className={
                      tx.type === "redeem"
                        ? "flex h-12 w-12 items-center justify-center rounded-full bg-orange-50 text-2xl"
                        : tx.type === "bonus"
                        ? "flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-2xl"
                        : "flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-2xl"
                    }
                  >
                    {tx.emoji}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-[14px] font-bold text-slate-800">
                      {tx.title}
                    </h4>
                    <p className="text-[11px] text-slate-400">
                      {tx.shop}
                      {tx.amount ? ` · ${tx.amount}` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={
                        tx.points >= 0
                          ? "font-headline text-[16px] font-bold text-brand-orange"
                          : "font-headline text-[16px] font-bold text-red-500"
                      }
                    >
                      {tx.points >= 0 ? "+" : ""}
                      {tx.points}
                    </p>
                    <p className="text-[11px] text-slate-400">{tx.time}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </article>
              ))}
            </div>
          </section>
        ))}

        <div className="pt-2 text-center">
          <button
            type="button"
            className="text-[14px] font-semibold text-brand-indigo hover:underline"
          >
            Tải thêm giao dịch ↓
          </button>
        </div>
      </main>
    </>
  );
}
