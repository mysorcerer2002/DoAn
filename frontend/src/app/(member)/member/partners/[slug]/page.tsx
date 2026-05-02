"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Clock,
  Globe,
  Loader2,
  Mail,
  MapPin,
  Phone,
  X,
} from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";
import { PartnerLedgerList } from "@/components/member/partner-ledger-list";

type PartnerDetail = {
  id: number;
  slug: string;
  name: string;
  category: string;
  description: string | null;
  logo_url: string | null;
  banner_url: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  address: string | null;
  business_hours: string | null;
  website: string | null;
  tax_code: string | null;
  is_member: boolean;
  points_balance: number | null;
  total_points_earned: number | null;
  current_tier_name: string | null;
  joined_at: string | null;
  last_activity_at: string | null;
};

type PartnerReward = {
  id: number;
  name: string;
  description: string | null;
  offer_type: string;
  points_cost: number;
  stock: number | null;
  image_url: string | null;
  valid_from: string | null;
  valid_until: string | null;
  user_points_balance: number;
  can_redeem: boolean;
};

const TIER_EMOJI: Record<string, string> = {
  Bronze: "🥉",
  Silver: "🥈",
  Gold: "🥇",
  Platinum: "💎",
};

const CATEGORY_LABEL: Record<string, string> = {
  cafe: "Cafe",
  food: "Ăn uống",
  retail: "Bán lẻ",
  beauty: "Mỹ phẩm",
  other: "Khác",
};

type TabId = "rewards" | "info" | "history";

const TABS: { id: TabId; label: string }[] = [
  { id: "rewards", label: "Ưu đãi" },
  { id: "info", label: "Thông tin" },
  { id: "history", label: "Lịch sử tích điểm" },
];

export default function PartnerDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;
  const [activeTab, setActiveTab] = useState<TabId>("rewards");

  const { data, isLoading, error } = useQuery({
    queryKey: ["partner-detail", slug],
    queryFn: async () => {
      const resp = await api.get<PartnerDetail>(`/users/me/partners/${slug}`);
      return resp.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-indigo border-t-transparent" />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="p-8 text-center text-slate-500">
        Không tìm thấy đối tác.
      </div>
    );
  }

  const hasMembership = data.is_member;

  return (
    <div className="pb-24">
      {/* Banner + back button overlay */}
      <div className="relative">
        {data.banner_url ? (
          <img
            src={data.banner_url}
            alt={`Ảnh bìa ${data.name}`}
            className="h-56 w-full object-cover"
          />
        ) : (
          <div className="h-56 w-full bg-gradient-to-br from-brand-indigo via-brand-violet to-brand-orange" />
        )}
        <Link
          href="/member/partners"
          className="absolute left-3 top-3 flex h-11 w-11 items-center justify-center rounded-full bg-white/90 text-slate-700 shadow-sm backdrop-blur hover:bg-white"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
      </div>

      {/* Card name overlap banner */}
      <section className="relative -mt-8 px-4">
        <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
          <div className="flex items-start gap-3">
            <div className="-mt-12 h-20 w-20 shrink-0 overflow-hidden rounded-2xl bg-white p-1 shadow-md ring-1 ring-slate-100">
              {data.logo_url ? (
                <img
                  src={data.logo_url}
                  alt={data.name}
                  className="h-full w-full rounded-xl object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center rounded-xl bg-slate-100 text-2xl">
                  🏪
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="font-headline text-[18px] font-bold leading-tight text-slate-800">
                {data.name}
              </h1>
              <span className="mt-1 inline-block rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
                {CATEGORY_LABEL[data.category] ?? data.category}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Hero: Điểm + Tier (chỉ hiện khi đã member) */}
      {hasMembership && (
        <section className="space-y-3 p-4">
          <div className="rounded-2xl bg-gradient-to-br from-brand-indigo to-brand-violet p-4">
            <p className="text-[11px] font-medium text-indigo-100/80">Điểm khả dụng</p>
            <p className="font-headline text-[40px] font-bold leading-none text-brand-orange">
              {data.points_balance?.toLocaleString("vi-VN")}
            </p>
          </div>
          {data.current_tier_name && (
            <div className="flex items-center gap-2 text-[13px] text-slate-700">
              <span className="text-2xl">
                {TIER_EMOJI[data.current_tier_name] ?? "🎖️"}
              </span>
              <span>
                Hạng hiện tại:{" "}
                <strong className="font-semibold">{data.current_tier_name}</strong>
              </span>
            </div>
          )}
        </section>
      )}

      {/* Tabs */}
      <div className="sticky top-16 z-30 flex border-b border-slate-100 bg-slate-50/95 backdrop-blur">
        {TABS.map((t) => {
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id)}
              className={
                isActive
                  ? "flex-1 border-b-2 border-brand-indigo px-2 py-3 text-[13px] font-bold text-brand-indigo"
                  : "flex-1 border-b-2 border-transparent px-2 py-3 text-[13px] font-medium text-slate-500"
              }
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {activeTab === "rewards" && <RewardsTab slug={slug} />}
      {activeTab === "info" && <InfoTab data={data} />}
      {activeTab === "history" && (
        <section className="p-4">
          {hasMembership ? (
            <PartnerLedgerList partnerSlug={slug} />
          ) : (
            <p className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-[13px] text-slate-500">
              Bạn chưa có giao dịch tại đối tác này.
            </p>
          )}
        </section>
      )}
    </div>
  );
}

function getErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    if (resp?.data?.detail) return resp.data.detail;
  }
  return "Đổi quà thất bại. Vui lòng thử lại.";
}

function RewardsTab({ slug }: { slug: string }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [confirmReward, setConfirmReward] = useState<PartnerReward | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const isFree = (r: PartnerReward) => r.points_cost === 0;

  const { data: rewards, isLoading, isError } = useQuery({
    queryKey: ["partner-rewards", slug],
    queryFn: async () => {
      const resp = await api.get<PartnerReward[]>(
        `/users/me/partners/${slug}/rewards`
      );
      return resp.data;
    },
  });

  const redeem = useMutation<{ id: number; redemption_code: string }, unknown, number>({
    mutationFn: async (reward_id: number) => {
      const res = await api.post<{ id: number; redemption_code: string }>(
        "/users/me/redemptions",
        { reward_id }
      );
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner-rewards", slug] });
      qc.invalidateQueries({ queryKey: ["partner-detail", slug] });
      qc.invalidateQueries({ queryKey: ["member", "memberships"] });
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      qc.invalidateQueries({ queryKey: ["customer", "ledger"] });
    },
  });

  const claimFree = useMutation<{ data: { id: number; redemption_code: string } }, unknown, number>({
    mutationFn: async (reward_id: number) => {
      const res = await api.post<{ id: number; redemption_code: string }>(
        `/users/me/rewards/${reward_id}/claim`
      );
      return { data: res.data };
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["partner-rewards", slug] });
      qc.invalidateQueries({ queryKey: ["partner-detail", slug] });
    },
  });

  function handleConfirm() {
    if (!confirmReward) return;
    setErrorMsg(null);
    if (isFree(confirmReward)) {
      claimFree.mutate(confirmReward.id, {
        onSuccess: (res) => {
          setConfirmReward(null);
          router.push(`/member/vouchers/${res.data.id}`);
        },
        onError: (err) => {
          setErrorMsg(getErrorMessage(err));
        },
      });
    } else {
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
  }

  if (isLoading) {
    return (
      <p className="p-4 text-center text-[13px] text-slate-400">Đang tải...</p>
    );
  }
  if (isError) {
    return (
      <p className="p-4 text-center text-[13px] text-red-600">
        Không tải được danh sách ưu đãi
      </p>
    );
  }
  if (!rewards || rewards.length === 0) {
    return (
      <p className="p-6 text-center text-[13px] text-slate-500">
        Đối tác chưa có ưu đãi nào.
      </p>
    );
  }

  return (
    <>
      <section className="space-y-3 p-4">
        {rewards.map((r) => {
          const missing = r.points_cost - r.user_points_balance;
          return (
            <article
              key={r.id}
              className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-3xl">
                  🎁
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-headline text-[14px] font-bold text-slate-800">
                    {r.name}
                  </h3>
                  {r.description && (
                    <p className="mt-0.5 line-clamp-2 text-[12px] text-slate-500">
                      {r.description}
                    </p>
                  )}
                  {isFree(r) ? (
                    <span className="mt-1 inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-700">
                      Miễn phí
                    </span>
                  ) : (
                    <p className="mt-1 font-headline text-[14px] font-bold text-brand-orange">
                      {r.points_cost.toLocaleString("vi-VN")} điểm
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between">
                {r.stock !== null && r.stock > 0 && r.stock <= 5 && (
                  <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-bold text-brand-orange">
                    Còn {r.stock}
                  </span>
                )}
                {r.can_redeem ? (
                  <button
                    type="button"
                    onClick={() => {
                      setErrorMsg(null);
                      setConfirmReward(r);
                    }}
                    className={
                      isFree(r)
                        ? "ml-auto rounded-full bg-emerald-600 px-4 py-1.5 text-[12px] font-bold text-white shadow-sm active:scale-95"
                        : "ml-auto rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white shadow-sm active:scale-95"
                    }
                  >
                    {isFree(r) ? "Nhận ngay" : "Đổi ngay"}
                  </button>
                ) : (
                  <span className="ml-auto text-[12px] font-medium text-slate-500">
                    Tích thêm {missing.toLocaleString("vi-VN")} điểm để đổi
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </section>

      {confirmReward && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 px-4 pb-4 pt-24"
          onClick={() => {
            if (!redeem.isPending && !claimFree.isPending) setConfirmReward(null);
          }}
        >
          <div
            className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <h3 className="font-headline text-[18px] font-bold text-slate-800">
                {isFree(confirmReward) ? "Nhận voucher miễn phí" : "Xác nhận đổi quà"}
              </h3>
              <button
                type="button"
                onClick={() => setConfirmReward(null)}
                disabled={redeem.isPending || claimFree.isPending}
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
              {isFree(confirmReward) ? (
                <div className="flex items-center justify-between border-t border-slate-200 pt-3">
                  <span className="text-[12px] text-slate-500">Chi phí</span>
                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[12px] font-bold text-emerald-700">
                    Miễn phí
                  </span>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between border-t border-slate-200 pt-3">
                    <span className="text-[12px] text-slate-500">Số điểm trừ</span>
                    <span className="font-headline text-[16px] font-bold text-brand-orange">
                      -{confirmReward.points_cost.toLocaleString("vi-VN")} điểm
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-slate-500">Số dư còn lại</span>
                    <span className="text-[13px] font-bold text-slate-800">
                      {(
                        confirmReward.user_points_balance - confirmReward.points_cost
                      ).toLocaleString("vi-VN")} điểm
                    </span>
                  </div>
                </>
              )}
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
                disabled={redeem.isPending || claimFree.isPending}
                className="flex-1 rounded-full border border-slate-200 bg-white py-3 text-[14px] font-bold text-slate-700 disabled:opacity-50"
              >
                Huỷ
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={redeem.isPending || claimFree.isPending}
                className={
                  isFree(confirmReward)
                    ? "flex-1 rounded-full bg-emerald-600 py-3 text-[14px] font-bold text-white shadow-md active:scale-[0.98] disabled:opacity-60"
                    : "flex-1 rounded-full bg-brand-indigo py-3 text-[14px] font-bold text-white shadow-md active:scale-[0.98] disabled:opacity-60"
                }
              >
                {(redeem.isPending || claimFree.isPending) ? (
                  <span className="inline-flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {isFree(confirmReward) ? "Đang nhận…" : "Đang đổi…"}
                  </span>
                ) : (
                  isFree(confirmReward) ? "Xác nhận nhận" : "Xác nhận đổi"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function InfoTab({ data }: { data: PartnerDetail }) {
  const hasContact =
    data.address ||
    data.contact_phone ||
    data.contact_email ||
    data.business_hours ||
    data.website;

  return (
    <section className="space-y-5 p-4">
      {data.description && (
        <div>
          <h3 className="font-headline text-[15px] font-bold text-slate-800">
            Giới thiệu
          </h3>
          <p className="mt-2 whitespace-pre-line text-[13px] leading-relaxed text-slate-600">
            {data.description}
          </p>
        </div>
      )}

      {hasContact && (
        <div>
          <h3 className="font-headline text-[15px] font-bold text-slate-800">
            Liên hệ
          </h3>
          <div className="mt-2 space-y-2 text-[13px]">
            {data.address && (
              <div className="flex items-start gap-2 text-slate-600">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-brand-indigo" />
                <span>{data.address}</span>
              </div>
            )}
            {data.contact_phone && (
              <div className="flex items-center gap-2 text-slate-600">
                <Phone className="h-4 w-4 shrink-0 text-brand-indigo" />
                <a href={`tel:${data.contact_phone}`} className="hover:underline">
                  {data.contact_phone}
                </a>
              </div>
            )}
            {data.contact_email && (
              <div className="flex items-center gap-2 text-slate-600">
                <Mail className="h-4 w-4 shrink-0 text-brand-indigo" />
                <a href={`mailto:${data.contact_email}`} className="hover:underline">
                  {data.contact_email}
                </a>
              </div>
            )}
            {data.business_hours && (
              <div className="flex items-start gap-2 text-slate-600">
                <Clock className="mt-0.5 h-4 w-4 shrink-0 text-brand-indigo" />
                <span>{data.business_hours}</span>
              </div>
            )}
            {data.website && (
              <div className="flex items-center gap-2 text-slate-600">
                <Globe className="h-4 w-4 shrink-0 text-brand-indigo" />
                <a
                  href={data.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {data.website}
                </a>
              </div>
            )}
          </div>
        </div>
      )}

      {!data.description && !hasContact && (
        <p className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-[13px] text-slate-500">
          Đối tác chưa cập nhật thông tin chi tiết.
        </p>
      )}
    </section>
  );
}
