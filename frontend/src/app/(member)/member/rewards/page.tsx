"use client";

import { ArrowLeft, Crown, Gift, Loader2, Search, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useMyMemberships } from "@/lib/hooks/use-me";

interface MeRewardItem {
  id: number;
  partner_id: number;
  partner_name: string;
  partner_slug: string;
  name: string;
  description: string | null;
  points_cost: number;
  stock: number | null;
  image_url: string | null;
  user_points_balance: number;
  can_redeem: boolean;
}

function useMyRewards() {
  return useQuery<MeRewardItem[]>({
    queryKey: ["member", "rewards"],
    queryFn: async () => (await api.get<MeRewardItem[]>("/users/me/rewards")).data,
  });
}

interface RedeemResponse {
  id: number;
  redemption_code: string;
}

function useRedeemReward() {
  const qc = useQueryClient();
  return useMutation<RedeemResponse, unknown, number>({
    mutationFn: async (reward_id: number) => {
      const res = await api.post<RedeemResponse>("/users/me/redemptions", {
        reward_id,
      });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["member", "rewards"] });
      qc.invalidateQueries({ queryKey: ["member", "memberships"] });
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      qc.invalidateQueries({ queryKey: ["customer", "ledger"] });
    },
  });
}

const FALLBACK_COLORS = [
  "bg-orange-50",
  "bg-indigo-50",
  "bg-violet-50",
  "bg-pink-50",
  "bg-amber-50",
  "bg-emerald-50",
];

function pickEmoji(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes("cafe") || lower.includes("latte")) return "☕";
  if (lower.includes("trà")) return "🍵";
  if (lower.includes("bánh")) return "🍰";
  if (lower.includes("voucher")) return "🎫";
  if (lower.includes("quà") || lower.includes("gift")) return "🎁";
  if (lower.includes("sữa")) return "🥤";
  if (lower.includes("topping")) return "✨";
  return "🎁";
}

function getErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    if (resp?.data?.detail) return resp.data.detail;
  }
  return "Đổi quà thất bại. Vui lòng thử lại.";
}

export default function RewardsPage() {
  const router = useRouter();
  const { data: memberships } = useMyMemberships();
  const { data: rewards, isLoading, isError } = useMyRewards();
  const redeem = useRedeemReward();
  const [search, setSearch] = useState("");
  const [partnerFilter, setPartnerFilter] = useState<number | null>(null);
  const [confirmReward, setConfirmReward] = useState<MeRewardItem | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const partners = useMemo(() => {
    const map = new Map<number, string>();
    (rewards ?? []).forEach((r) => map.set(r.partner_id, r.partner_name));
    return Array.from(map, ([id, name]) => ({ id, name }));
  }, [rewards]);

  const filtered = useMemo(() => {
    return (rewards ?? []).filter((r) => {
      if (partnerFilter != null && r.partner_id !== partnerFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          r.name.toLowerCase().includes(q) ||
          r.partner_name.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [rewards, partnerFilter, search]);

  // Ví toàn cục: mọi membership share cùng `points_balance` (global wallet)
  const totalPoints = (memberships ?? [])[0]?.points_balance ?? 0;
  const topTier = (memberships ?? [])
    .slice()
    .sort((a, b) => b.lifetime_earned - a.lifetime_earned)[0];

  function handleConfirmRedeem() {
    if (!confirmReward) return;
    setErrorMsg(null);
    redeem.mutate(confirmReward.id, {
      onSuccess: (data) => {
        setConfirmReward(null);
        router.push(`/member/vouchers/${data.id}`);
      },
      onError: (err) => {
        setErrorMsg(getErrorMessage(err));
      },
    });
  }

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
          Đổi quà
        </h1>
        <div className="w-10" />
      </header>

      <main className="space-y-4 px-4 pt-2 pb-8">
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-indigo to-brand-violet p-4 shadow-xl shadow-indigo-200">
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 flex items-center justify-between">
            <div>
              <p className="text-[12px] font-medium text-indigo-100">
                Điểm hiện có
              </p>
              <div className="flex items-baseline gap-2">
                <span className="font-headline text-[32px] font-bold leading-none text-brand-orange">
                  {totalPoints.toLocaleString("vi-VN")}
                </span>
                <span className="text-[12px] text-indigo-100">điểm</span>
              </div>
              <p className="mt-1 text-[10px] text-indigo-100/80">
                Ví toàn cục — dùng được tại mọi đối tác
              </p>
            </div>
            {topTier?.current_tier_name && (
              <div className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
                <Crown className="h-3.5 w-3.5 text-white" fill="white" />
                <span className="font-headline text-[12px] font-bold text-white">
                  {topTier.current_tier_name}
                </span>
              </div>
            )}
          </div>
        </section>

        <section className="relative">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm quà theo tên hoặc đối tác"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </section>

        {partners.length > 0 && (
          <section className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
            <button
              type="button"
              onClick={() => setPartnerFilter(null)}
              className={
                partnerFilter === null
                  ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                  : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
              }
            >
              Tất cả ({rewards?.length ?? 0})
            </button>
            {partners.map((t) => {
              const count = (rewards ?? []).filter(
                (r) => r.partner_id === t.id
              ).length;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setPartnerFilter(t.id)}
                  className={
                    partnerFilter === t.id
                      ? "shrink-0 rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white"
                      : "shrink-0 rounded-full border border-brand-indigo/30 bg-white px-4 py-1.5 text-[12px] font-medium text-brand-indigo"
                  }
                >
                  {t.name} ({count})
                </button>
              );
            })}
          </section>
        )}

        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="rounded-xl bg-red-50 p-4 text-center text-[13px] text-red-600">
            Không tải được danh sách quà
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
            <Gift className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              {search
                ? "Không tìm thấy quà phù hợp"
                : memberships?.length === 0
                  ? "Chưa có giao dịch tại đối tác nào"
                  : "Chưa có quà nào"}
            </p>
            {memberships?.length === 0 && (
              <Link
                href="/member/partners"
                className="mt-3 inline-block text-[13px] font-bold text-brand-indigo hover:underline"
              >
                Khám phá đối tác →
              </Link>
            )}
          </div>
        ) : (
          <section className="grid grid-cols-2 gap-3">
            {filtered.map((r, idx) => (
              <article
                key={r.id}
                className={
                  r.can_redeem
                    ? "relative overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm"
                    : "relative overflow-hidden rounded-2xl border border-slate-100 bg-white opacity-60 shadow-sm"
                }
              >
                {r.stock !== null && r.stock > 0 && r.stock <= 5 && (
                  <span className="absolute right-2 top-2 z-10 rounded-full bg-brand-orange px-2 py-0.5 text-[9px] font-bold text-white">
                    Còn {r.stock}
                  </span>
                )}
                <div
                  className={`flex aspect-square w-full items-center justify-center text-6xl ${FALLBACK_COLORS[idx % FALLBACK_COLORS.length]}`}
                >
                  {pickEmoji(r.name)}
                </div>
                <div className="space-y-1 p-3">
                  <h4 className="line-clamp-2 min-h-[2.4rem] font-headline text-[14px] font-bold leading-tight text-slate-800">
                    {r.name}
                  </h4>
                  <p className="truncate text-[11px] text-slate-400">
                    {r.partner_name}
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="font-headline text-[14px] font-bold text-brand-orange">
                      {r.points_cost.toLocaleString("vi-VN")}đ
                    </span>
                    {r.can_redeem ? (
                      <button
                        type="button"
                        onClick={() => {
                          setErrorMsg(null);
                          setConfirmReward(r);
                        }}
                        className="rounded-full bg-brand-indigo px-3 py-1 text-[11px] font-bold text-white shadow-sm active:scale-95"
                      >
                        Đổi
                      </button>
                    ) : (
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500">
                        Thiếu {(r.points_cost - r.user_points_balance).toLocaleString("vi-VN")}đ
                      </span>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      {confirmReward && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 px-4 pb-4 pt-24"
          onClick={() => {
            if (!redeem.isPending) setConfirmReward(null);
          }}
        >
          <div
            className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <h3 className="font-headline text-[18px] font-bold text-slate-800">
                Xác nhận đổi quà
              </h3>
              <button
                type="button"
                onClick={() => setConfirmReward(null)}
                disabled={redeem.isPending}
                className="text-slate-400 hover:text-slate-600 disabled:opacity-50"
                aria-label="Đóng"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-4 space-y-3 rounded-xl bg-slate-50 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-slate-500">Quà</span>
                <span className="text-right text-[13px] font-bold text-slate-800">
                  {confirmReward.name}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-slate-500">Đối tác</span>
                <span className="text-[13px] text-slate-700">
                  {confirmReward.partner_name}
                </span>
              </div>
              <div className="flex items-center justify-between border-t border-slate-200 pt-3">
                <span className="text-[12px] text-slate-500">Số điểm trừ</span>
                <span className="font-headline text-[16px] font-bold text-brand-orange">
                  -{confirmReward.points_cost.toLocaleString("vi-VN")}đ
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-slate-500">Số dư còn lại</span>
                <span className="text-[13px] font-bold text-slate-800">
                  {(totalPoints - confirmReward.points_cost).toLocaleString("vi-VN")}đ
                </span>
              </div>
            </div>
            {errorMsg && (
              <p className="mt-3 rounded-lg bg-red-50 p-3 text-[12px] text-red-600">
                {errorMsg}
              </p>
            )}
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setConfirmReward(null)}
                disabled={redeem.isPending}
                className="flex-1 rounded-full border border-slate-200 bg-white py-3 text-[14px] font-bold text-slate-700 disabled:opacity-50"
              >
                Huỷ
              </button>
              <button
                type="button"
                onClick={handleConfirmRedeem}
                disabled={redeem.isPending}
                className="flex-1 rounded-full bg-brand-indigo py-3 text-[14px] font-bold text-white shadow-md active:scale-[0.98] disabled:opacity-60"
              >
                {redeem.isPending ? (
                  <span className="inline-flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Đang đổi…
                  </span>
                ) : (
                  "Xác nhận đổi"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
