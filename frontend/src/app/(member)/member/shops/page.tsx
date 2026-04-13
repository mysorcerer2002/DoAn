"use client";

import { ArrowLeft, Crown, Loader2, Search, Store } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "@/lib/api";

type TenantCategory = "cafe" | "food" | "retail" | "beauty" | "other";

interface ShopItem {
  id: number;
  name: string;
  slug: string;
  category: TenantCategory;
  description: string | null;
  logo_url: string | null;
  is_member: boolean;
  points_balance: number | null;
  tier_name: string | null;
}

const CATEGORY_META: Record<
  TenantCategory,
  { label: string; emoji: string; bgColor: string; accentColor: string }
> = {
  cafe: {
    label: "Cafe",
    emoji: "☕",
    bgColor: "bg-orange-50",
    accentColor: "text-amber-700",
  },
  food: {
    label: "Ăn uống",
    emoji: "🍜",
    bgColor: "bg-red-50",
    accentColor: "text-red-600",
  },
  retail: {
    label: "Bán lẻ",
    emoji: "🛍️",
    bgColor: "bg-indigo-50",
    accentColor: "text-brand-indigo",
  },
  beauty: {
    label: "Mỹ phẩm",
    emoji: "💄",
    bgColor: "bg-pink-50",
    accentColor: "text-pink-600",
  },
  other: {
    label: "Khác",
    emoji: "🏪",
    bgColor: "bg-slate-50",
    accentColor: "text-slate-600",
  },
};

const CATEGORY_PILLS: Array<{ id: "all" | TenantCategory; label: string; emoji: string | null }> = [
  { id: "all", label: "Tất cả", emoji: null },
  { id: "cafe", label: "Cafe", emoji: "☕" },
  { id: "food", label: "Ăn uống", emoji: "🍜" },
  { id: "retail", label: "Bán lẻ", emoji: "🛍️" },
  { id: "beauty", label: "Mỹ phẩm", emoji: "💄" },
];

function useShops() {
  return useQuery<ShopItem[]>({
    queryKey: ["member", "shops"],
    queryFn: async () => (await api.get<ShopItem[]>("/users/me/shops")).data,
  });
}

export default function ShopsPage() {
  const { data: shops, isLoading, isError } = useShops();
  const [categoryFilter, setCategoryFilter] = useState<"all" | TenantCategory>("all");
  const [membershipFilter, setMembershipFilter] = useState<
    "all" | "joined" | "new"
  >("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return (shops ?? []).filter((s) => {
      if (categoryFilter !== "all" && s.category !== categoryFilter) return false;
      if (membershipFilter === "joined" && !s.is_member) return false;
      if (membershipFilter === "new" && s.is_member) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          (s.description ?? "").toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [shops, categoryFilter, membershipFilter, search]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    (shops ?? []).forEach((s) => {
      counts[s.category] = (counts[s.category] ?? 0) + 1;
    });
    return counts;
  }, [shops]);

  const joinedCount = (shops ?? []).filter((s) => s.is_member).length;

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
          Cửa hàng
        </h1>
        <div className="w-10" />
      </header>

      <main className="space-y-4 px-4 pt-2 pb-8">
        {/* Stats mini */}
        <section className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <p className="text-[11px] font-medium text-slate-400">Đang là thành viên</p>
            <p className="mt-1 font-headline text-[24px] font-bold text-brand-indigo">
              {joinedCount}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <p className="text-[11px] font-medium text-slate-400">Tổng shop</p>
            <p className="mt-1 font-headline text-[24px] font-bold text-brand-orange">
              {shops?.length ?? 0}
            </p>
          </div>
        </section>

        {/* Search */}
        <section className="relative">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm shop theo tên"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </section>

        {/* Category pills */}
        <section className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
          {CATEGORY_PILLS.map((f) => {
            const count =
              f.id === "all" ? shops?.length ?? 0 : categoryCounts[f.id] ?? 0;
            return (
              <button
                key={f.id}
                type="button"
                onClick={() => setCategoryFilter(f.id)}
                className={
                  categoryFilter === f.id
                    ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                    : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
                }
              >
                {f.emoji ? `${f.emoji} ${f.label}` : f.label} ({count})
              </button>
            );
          })}
        </section>

        {/* Membership filter */}
        <section className="flex gap-2">
          {(
            [
              { id: "all", label: "Tất cả" },
              { id: "joined", label: "Đã tham gia" },
              { id: "new", label: "Chưa tham gia" },
            ] as const
          ).map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setMembershipFilter(f.id)}
              className={
                membershipFilter === f.id
                  ? "rounded-full bg-brand-violet px-4 py-1.5 text-[12px] font-bold text-white"
                  : "rounded-full border border-brand-violet/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-violet"
              }
            >
              {f.label}
            </button>
          ))}
        </section>

        {/* Shops list */}
        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-[13px] text-red-600">
            Không tải được danh sách cửa hàng
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
            <Store className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              {search ? "Không tìm thấy cửa hàng" : "Chưa có cửa hàng nào"}
            </p>
          </div>
        ) : (
          <section className="space-y-3">
            {filtered.map((s) => {
              const meta = CATEGORY_META[s.category] ?? CATEGORY_META.other;
              return (
              <article
                key={s.id}
                className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              >
                <div
                  className={`flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl text-4xl ${meta.bgColor}`}
                >
                  {meta.emoji}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="truncate font-headline text-[15px] font-bold text-slate-800">
                      {s.name}
                    </h3>
                    {s.is_member && s.tier_name && (
                      <span className="inline-flex flex-shrink-0 items-center gap-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-2 py-0.5 text-[10px] font-bold text-white">
                        <Crown className="h-2.5 w-2.5" fill="white" />
                        {s.tier_name}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[11px] font-bold ${meta.accentColor}`}>
                      {meta.label}
                    </span>
                    {s.description && (
                      <span className="truncate text-[11px] text-slate-400">
                        · {s.description}
                      </span>
                    )}
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    {s.is_member ? (
                      <span className="font-headline text-[14px] font-bold text-brand-orange">
                        {s.points_balance?.toLocaleString("vi-VN") ?? 0} điểm
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400">
                        Chưa tham gia
                      </span>
                    )}
                    <button
                      type="button"
                      disabled={s.is_member}
                      className={
                        s.is_member
                          ? "rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-500"
                          : "rounded-full bg-brand-indigo px-3 py-1 text-[11px] font-bold text-white active:scale-95"
                      }
                    >
                      {s.is_member ? "Đã là thành viên" : "Tham gia"}
                    </button>
                  </div>
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
