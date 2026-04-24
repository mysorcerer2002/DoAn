"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

type LedgerEntry = {
  id: number;
  reason: string;
  delta: number;
  balance_after: number;
  ref_type: string | null;
  created_at: string;
};

const PAGE_LIMIT = 20;

const REASON_LABEL: Record<string, string> = {
  earn: "Tích điểm",
  redeem: "Đổi quà",
  expire: "Hết hạn",
  adjust: "Điều chỉnh",
  refund: "Hoàn điểm",
};

export function PartnerLedgerList({ partnerSlug }: { partnerSlug: string }) {
  const { data, fetchNextPage, hasNextPage, isLoading } = useInfiniteQuery({
    queryKey: ["ledger", partnerSlug],
    queryFn: async ({ pageParam = 0 }) => {
      const resp = await api.get<LedgerEntry[]>(
        `/users/me/ledger?partner_slug=${partnerSlug}&limit=${PAGE_LIMIT}&offset=${pageParam}`
      );
      return { items: resp.data, offset: pageParam as number };
    },
    initialPageParam: 0,
    getNextPageParam: (last) =>
      last.items.length === PAGE_LIMIT ? last.offset + PAGE_LIMIT : undefined,
  });

  if (isLoading) {
    return <p className="text-[13px] text-slate-400">Đang tải...</p>;
  }

  const entries = data?.pages.flatMap((p) => p.items) ?? [];

  if (entries.length === 0) {
    return (
      <p className="text-[13px] text-slate-400">
        Chưa có giao dịch tích/đổi điểm.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <ul className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {entries.map((e) => (
          <li key={e.id} className="flex items-start justify-between p-4">
            <div className="space-y-0.5">
              <p className="text-[13px] font-semibold text-slate-800">
                {REASON_LABEL[e.reason] ?? e.reason}
              </p>
              <p className="text-[11px] text-slate-400">
                {new Date(e.created_at).toLocaleString("vi-VN")}
              </p>
              <p className="text-[11px] text-slate-400">
                Còn lại: {e.balance_after.toLocaleString("vi-VN")}
              </p>
            </div>
            <span
              className={`font-headline text-[16px] font-bold ${
                e.delta > 0 ? "text-brand-orange" : "text-red-500"
              }`}
            >
              {e.delta > 0 ? "+" : ""}
              {e.delta.toLocaleString("vi-VN")}
            </span>
          </li>
        ))}
      </ul>
      {hasNextPage && (
        <button
          type="button"
          className="w-full rounded-xl border border-slate-100 bg-white py-3 text-[13px] font-medium text-brand-indigo shadow-sm active:scale-[0.99]"
          onClick={() => fetchNextPage()}
        >
          Xem thêm
        </button>
      )}
    </div>
  );
}
