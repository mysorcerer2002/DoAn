import { ArrowLeft, MapPin, Search, Star } from "lucide-react";
import Link from "next/link";

type Shop = {
  id: string;
  name: string;
  address: string;
  emoji: string;
  bgColor: string;
  rating: number;
  reviews: number;
  distance: string;
  pointRate: string;
  status: "join" | "joined";
  joinedTier?: { label: string; tone: "indigo" | "slate" };
  badge?: string;
  highlight?: string;
};

const shops: Shop[] = [
  {
    id: "s1",
    name: "Cafe Cộng - Bà Triệu",
    address: "12 Bà Triệu, Hai Bà Trưng, HN",
    emoji: "☕",
    bgColor: "bg-orange-50",
    rating: 4.8,
    reviews: 124,
    distance: "1.2 km",
    pointRate: "1₫ = 0.01 điểm",
    status: "join",
  },
  {
    id: "s2",
    name: "Trà sữa Toko",
    address: "45 Cầu Giấy, HN",
    emoji: "🥤",
    bgColor: "bg-violet-50",
    rating: 4.6,
    reviews: 89,
    distance: "800 m",
    pointRate: "1₫ = 0.012 điểm",
    status: "join",
    badge: "MỚI",
  },
  {
    id: "s3",
    name: "BBQ Hàn Quốc",
    address: "78 Đống Đa, HN",
    emoji: "🍜",
    bgColor: "bg-amber-50",
    rating: 4.9,
    reviews: 256,
    distance: "2.5 km",
    pointRate: "1₫ = 0.01 điểm",
    status: "join",
    highlight: "🎁 Có 5 quà tặng mới",
  },
  {
    id: "s4",
    name: "Mỹ phẩm Cocoon",
    address: "23 Hoàn Kiếm, HN",
    emoji: "🛍️",
    bgColor: "bg-pink-50",
    rating: 4.7,
    reviews: 178,
    distance: "3.0 km",
    pointRate: "1₫ = 0.015 điểm",
    status: "joined",
    joinedTier: { label: "Hạng Bạc", tone: "slate" },
  },
  {
    id: "s5",
    name: "Pizza Hut",
    address: "56 Nguyễn Du, HN",
    emoji: "🍕",
    bgColor: "bg-red-50",
    rating: 4.5,
    reviews: 312,
    distance: "3.2 km",
    pointRate: "1₫ = 0.01 điểm",
    status: "join",
    highlight: "Khuyến mãi tháng 4",
  },
];

const filters = [
  { id: "all", label: "Tất cả", emoji: null },
  { id: "cafe", label: "Cafe", emoji: "☕" },
  { id: "food", label: "Nhà hàng", emoji: "🍜" },
  { id: "retail", label: "Bán lẻ", emoji: "🛍️" },
  { id: "drink", label: "Đồ uống", emoji: "🥤" },
  { id: "new", label: "Mới", emoji: "✨" },
] as const;

export default function ShopsPage() {
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
          Khám phá cửa hàng
        </h1>
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-[#6366F1] hover:bg-indigo-50"
          aria-label="Vị trí"
        >
          <MapPin className="h-6 w-6" />
        </button>
      </header>

      <main className="space-y-4 px-4 pt-2">
        <div className="relative">
          <Search className="pointer-events-none absolute inset-y-0 left-4 my-auto h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm cửa hàng..."
            className="block w-full rounded-full border border-slate-200 bg-white py-3 pl-12 pr-4 text-[14px] outline-none placeholder:text-slate-400 focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/20"
          />
        </div>

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

        <section className="flex items-center gap-1 rounded-full bg-slate-100 p-1">
          <button
            type="button"
            className="flex-1 rounded-full bg-white px-4 py-2 text-[13px] font-bold text-slate-400 shadow-sm"
          >
            Đã tham gia (3)
          </button>
          <button
            type="button"
            className="flex-1 rounded-full bg-[#6366F1] px-4 py-2 text-[13px] font-bold text-white shadow"
          >
            Khám phá (12)
          </button>
        </section>

        <div className="space-y-3 pb-4">
          {shops.map((shop) => (
            <article
              key={shop.id}
              className="relative rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
            >
              {shop.badge && (
                <span className="absolute right-4 top-4 rounded-full bg-[#FB923C] px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                  {shop.badge}
                </span>
              )}
              <div className="flex items-start gap-3">
                <div
                  className={`flex h-14 w-14 items-center justify-center rounded-2xl text-3xl ${shop.bgColor}`}
                >
                  {shop.emoji}
                </div>
                <div className="flex-1 space-y-1">
                  <h3 className="text-[15px] font-bold text-slate-800">
                    {shop.name}
                  </h3>
                  <p className="flex items-center gap-1 text-[11px] text-slate-400">
                    <MapPin className="h-3 w-3" />
                    {shop.address}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-500">
                    <span className="flex items-center gap-0.5">
                      <Star
                        className="h-3 w-3 text-amber-400"
                        fill="currentColor"
                      />
                      <span className="font-bold text-slate-700">
                        {shop.rating}
                      </span>
                      <span className="text-slate-400">
                        ({shop.reviews})
                      </span>
                    </span>
                    <span>·</span>
                    <span>{shop.distance}</span>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                    <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-medium text-[#6366F1]">
                      {shop.pointRate}
                    </span>
                    {shop.highlight && (
                      <span className="rounded-full bg-orange-50 px-2 py-0.5 text-[10px] font-medium text-[#FB923C]">
                        {shop.highlight}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-end gap-2">
                {shop.status === "joined" && shop.joinedTier ? (
                  <>
                    <span
                      className={
                        shop.joinedTier.tone === "indigo"
                          ? "rounded-full bg-indigo-50 px-3 py-1 text-[10px] font-bold uppercase text-[#6366F1]"
                          : "rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase text-slate-500"
                      }
                    >
                      {shop.joinedTier.label}
                    </span>
                    <button
                      type="button"
                      className="rounded-full border border-[#6366F1] px-4 py-1.5 text-[12px] font-bold text-[#6366F1]"
                    >
                      Xem chi tiết
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    className="rounded-full bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] px-4 py-1.5 text-[12px] font-bold text-white shadow-md shadow-indigo-200 active:scale-95"
                  >
                    + Tham gia
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}
