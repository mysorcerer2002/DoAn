"use client";

import { ArrowLeft, Loader2, Search, Store } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "@/lib/api";

type TenantCategory = "cafe" | "food" | "retail" | "beauty" | "other";

interface PartnerSummary {
  id: number;
  name: string;
  slug: string;
  category: TenantCategory;
  description: string | null;
  logo_url: string | null;
  is_member: boolean;
  points_balance: number | null;
  current_tier_name: string | null;
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

export default function MemberPartnersPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<"all" | TenantCategory>("all");

  const { data: partners = [], isLoading, isError } = useQuery<PartnerSummary[]>({
    queryKey: ["my-partners", search, category],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (category !== "all") params.set("category", category);
      const resp = await api.get<PartnerSummary[]>(
        `/users/me/partners?${params.toString()}`
      );
      return resp.data;
    },
  });

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
          Đối tác
        </h1>
        <div className="w-10" />
      </header>

      <main className="space-y-4 px-4 pt-2 pb-8">
        <p className="text-[13px] text-slate-500">
          Giao dịch tại bất kỳ đối tác nào để bắt đầu tích điểm.
        </p>

        {/* Search */}
        <section className="relative">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm đối tác theo tên"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </section>

        {/* Category pills */}
        <section className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
          {CATEGORY_PILLS.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCategory(c.id)}
              className={
                category === c.id
                  ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                  : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
              }
            >
              {c.emoji ? `${c.emoji} ${c.label}` : c.label}
            </button>
          ))}
        </section>

        {/* Partners list */}
        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-[13px] text-red-600">
            Không tải được danh sách đối tác
          </div>
        ) : partners.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
            <Store className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              {search ? "Không tìm thấy đối tác" : "Chưa có đối tác nào"}
            </p>
          </div>
        ) : (
          <section className="space-y-3">
            {partners.map((p) => {
              const meta = CATEGORY_META[p.category] ?? CATEGORY_META.other;
              return (
                <Link
                  key={p.id}
                  href={`/member/partners/${p.slug}`}
                  className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm active:scale-[0.99] transition-transform"
                >
                  <div
                    className={`flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl text-4xl ${meta.bgColor}`}
                  >
                    {meta.emoji}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate font-headline text-[15px] font-bold text-slate-800">
                      {p.name}
                    </h3>
                    <span className={`text-[11px] font-bold ${meta.accentColor}`}>
                      {meta.label}
                    </span>
                    {p.is_member ? (
                      <div className="mt-1 flex items-center gap-2">
                        {p.current_tier_name && (
                          <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-700">
                            ⭐ {p.current_tier_name}
                          </span>
                        )}
                        <span className="text-[11px] font-bold text-brand-indigo">
                          {(p.points_balance ?? 0).toLocaleString("vi-VN")} điểm
                        </span>
                      </div>
                    ) : p.description ? (
                      <p className="truncate text-[11px] text-slate-400 mt-0.5">
                        {p.description}
                      </p>
                    ) : null}
                  </div>
                </Link>
              );
            })}
          </section>
        )}
      </main>
    </>
  );
}
