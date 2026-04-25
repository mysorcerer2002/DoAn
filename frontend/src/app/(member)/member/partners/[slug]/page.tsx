"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Clock, Globe, Mail, MapPin, Phone } from "lucide-react";
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
  points_cost: number;
  stock: number | null;
  image_url: string | null;
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
      {/* Header */}
      <header className="sticky top-0 z-40 flex h-16 items-center gap-2 bg-slate-50/95 px-4 backdrop-blur border-b border-slate-100">
        <Link
          href="/member/partners"
          className="flex h-10 w-10 items-center justify-center rounded-full text-brand-indigo hover:bg-indigo-50"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <h1 className="flex-1 truncate font-headline text-[17px] font-bold text-slate-800">
          {data.name}
        </h1>
        <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-600">
          {CATEGORY_LABEL[data.category] ?? data.category}
        </span>
      </header>

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

function RewardsTab({ slug }: { slug: string }) {
  const { data: rewards, isLoading, isError } = useQuery({
    queryKey: ["partner-rewards", slug],
    queryFn: async () => {
      const resp = await api.get<PartnerReward[]>(
        `/users/me/partners/${slug}/rewards`
      );
      return resp.data;
    },
  });

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
                <p className="mt-1 font-headline text-[14px] font-bold text-brand-orange">
                  {r.points_cost.toLocaleString("vi-VN")} điểm
                </p>
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
                  className="ml-auto rounded-full bg-brand-indigo px-4 py-1.5 text-[12px] font-bold text-white shadow-sm active:scale-95"
                >
                  Đổi ngay
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
  );
}

function InfoTab({ data }: { data: PartnerDetail }) {
  return (
    <section className="space-y-3 p-4">
      {data.logo_url && (
        <img
          src={data.logo_url}
          alt={data.name}
          className="h-24 w-24 rounded-2xl object-cover shadow-sm"
        />
      )}
      {data.description && (
        <p className="text-[13px] text-slate-500">{data.description}</p>
      )}
      <div className="space-y-2 text-[13px]">
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
    </section>
  );
}
