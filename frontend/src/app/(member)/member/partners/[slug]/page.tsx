"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Clock, Globe, Mail, MapPin, Phone } from "lucide-react";

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
  points_balance: number | null;
  total_points_earned: number | null;
  current_tier_name: string | null;
  joined_at: string | null;
  last_activity_at: string | null;
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

export default function PartnerDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);

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

  const hasMembership = data.points_balance !== null;

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

      {/* Section 1: Thông tin đối tác */}
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

      {/* Section 2: Điểm của bạn */}
      <section className="border-t border-slate-100 p-4 space-y-3">
        <h2 className="font-headline text-[16px] font-bold text-slate-800">
          Điểm của bạn tại đây
        </h2>
        {hasMembership ? (
          <div className="space-y-3">
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
            <div className="grid grid-cols-2 gap-3">
              {data.total_points_earned !== null && (
                <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
                  <p className="text-[11px] text-slate-400">Tổng đã tích</p>
                  <p className="font-headline text-[18px] font-bold text-slate-800">
                    {data.total_points_earned.toLocaleString("vi-VN")}
                  </p>
                </div>
              )}
              {data.joined_at && (
                <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
                  <p className="text-[11px] text-slate-400">Tham gia từ</p>
                  <p className="font-headline text-[14px] font-bold text-slate-800">
                    {new Date(data.joined_at).toLocaleDateString("vi-VN")}
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center">
            <p className="text-[13px] text-slate-500">
              Chưa có giao dịch tại đối tác này.
              <br />
              Hãy quét QR khi mua hàng để bắt đầu tích điểm.
            </p>
          </div>
        )}
      </section>

      {/* Section 3: Lịch sử */}
      {hasMembership && (
        <section className="border-t border-slate-100 p-4 space-y-3">
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Lịch sử tích/đổi điểm
          </h2>
          <PartnerLedgerList partnerSlug={slug} />
        </section>
      )}
    </div>
  );
}
