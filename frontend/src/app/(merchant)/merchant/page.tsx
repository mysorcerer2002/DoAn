"use client";

import {
  Calendar,
  Coins,
  CreditCard,
  Download,
  Loader2,
  Sparkles,
  TrendingUp,
  UserPlus,
} from "lucide-react";

import { useDashboard } from "@/lib/hooks/use-merchant";
import type {
  CampaignRoiPoint,
  DailyTransactionPoint,
  TierDistributionPoint,
} from "@/types/merchant";

function formatVnd(n: number): string {
  return n.toLocaleString("vi-VN") + " ₫";
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

export default function MerchantDashboardPage() {
  const { data, isLoading, isError } = useDashboard();

  if (isLoading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  if (isError || !data) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center px-8">
        <div className="max-w-md rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
          <p className="font-bold text-red-700">Không tải được dashboard</p>
          <p className="mt-2 text-[13px] text-red-600">
            Vui lòng thử lại hoặc kiểm tra kết nối backend.
          </p>
        </div>
      </main>
    );
  }

  const maxRevenue = Math.max(
    1,
    ...data.daily_transactions.map((d: DailyTransactionPoint) => d.total_revenue)
  );
  const totalMembers = data.tier_distribution.reduce(
    (s: number, t: TierDistributionPoint) => s + t.member_count,
    0
  );

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <h1 className="font-headline text-[32px] font-bold text-slate-800">
            Tổng quan
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Theo dõi hiệu quả tích điểm và khuyến mãi
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-[13px] font-medium text-slate-700 hover:border-brand-indigo"
          >
            <Calendar className="h-4 w-4 text-brand-indigo" />
            {formatDate(data.period_from)} - {formatDate(data.period_to)}
          </button>
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl border border-brand-indigo bg-white px-4 py-2.5 text-[13px] font-bold text-brand-indigo hover:bg-brand-indigo/5"
          >
            <Download className="h-4 w-4" />
            Xuất báo cáo
          </button>
        </div>
      </header>

      {/* KPI cards */}
      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard
          icon={TrendingUp}
          label="Doanh thu"
          value={formatVnd(data.total_revenue)}
          tone="indigo"
        />
        <KpiCard
          icon={CreditCard}
          label="Giao dịch"
          value={data.transaction_count.toLocaleString("vi-VN")}
          tone="indigo"
        />
        <KpiCard
          icon={UserPlus}
          label="Thành viên"
          value={data.member_count.toLocaleString("vi-VN")}
          tone="indigo"
        />
        <KpiCard
          icon={Coins}
          label="Đổi quà"
          value={data.total_redemption_count.toLocaleString("vi-VN")}
          tone="orange"
          sub={`Tỉ lệ: ${(data.redemption_rate * 100).toFixed(1)}%`}
        />
      </section>

      {/* Charts row */}
      <section className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <article className="col-span-2 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <header className="flex items-center justify-between">
            <div>
              <h2 className="font-headline text-[18px] font-bold text-slate-800">
                Doanh thu theo ngày
              </h2>
              <p className="text-[12px] text-slate-400">
                {data.daily_transactions.length} ngày
              </p>
            </div>
          </header>
          {data.daily_transactions.length === 0 ? (
            <div className="flex h-60 items-center justify-center text-[13px] text-slate-400">
              Chưa có dữ liệu giao dịch trong khoảng này
            </div>
          ) : (
            <RevenueLineChart
              data={data.daily_transactions}
              maxRevenue={maxRevenue}
            />
          )}
        </article>

        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <header>
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Hạng thành viên
            </h2>
            <p className="text-[12px] text-slate-400">
              {totalMembers} thành viên
            </p>
          </header>
          <TierDistributionList
            data={data.tier_distribution}
            total={totalMembers}
          />
        </article>
      </section>

      {/* Campaign ROI */}
      <section className="mt-5 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <header className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-brand-orange" />
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Top chiến dịch
          </h2>
        </header>
        <div className="mt-4">
          {data.campaign_roi.length === 0 ? (
            <p className="text-[13px] text-slate-400">
              Chưa có chiến dịch nào.
            </p>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full min-w-[700px]">
              <thead>
                <tr className="text-left text-[11px] font-bold uppercase text-slate-400">
                  <th className="pb-3">Chiến dịch</th>
                  <th className="pb-3 text-right">Đã phát</th>
                  <th className="pb-3 text-right">Đã dùng</th>
                  <th className="pb-3 text-right">Tổng giảm</th>
                  <th className="pb-3 text-right">Doanh thu</th>
                </tr>
              </thead>
              <tbody>
                {data.campaign_roi.map((c: CampaignRoiPoint) => (
                  <tr key={c.campaign_id} className="border-t border-slate-100">
                    <td className="py-3 text-[13px] font-bold text-slate-800">
                      {c.campaign_name}
                    </td>
                    <td className="py-3 text-right text-[13px]">
                      {c.vouchers_issued}
                    </td>
                    <td className="py-3 text-right text-[13px] font-bold text-emerald-600">
                      {c.vouchers_used}
                    </td>
                    <td className="py-3 text-right text-[13px] text-brand-orange">
                      {formatVnd(c.total_discount)}
                    </td>
                    <td className="py-3 text-right text-[13px] font-bold text-slate-800">
                      {formatVnd(c.total_revenue_from_voucher_txns)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

type KpiTone = "indigo" | "orange";

function KpiCard({
  icon: Icon,
  label,
  value,
  tone,
  sub,
}: {
  icon: typeof TrendingUp;
  label: string;
  value: string;
  tone: KpiTone;
  sub?: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div
          className={
            tone === "orange"
              ? "flex h-10 w-10 items-center justify-center rounded-xl bg-orange-50 text-brand-orange"
              : "flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-brand-indigo"
          }
        >
          <Icon className="h-5 w-5" />
        </div>
        <p className="text-[12px] font-medium text-slate-400">{label}</p>
      </div>
      <p
        className={
          tone === "orange"
            ? "mt-3 font-headline text-[26px] font-bold text-brand-orange"
            : "mt-3 font-headline text-[26px] font-bold text-slate-800"
        }
      >
        {value}
      </p>
      {sub && <p className="mt-1 text-[11px] text-slate-500">{sub}</p>}
    </article>
  );
}

function RevenueLineChart({
  data,
  maxRevenue,
}: {
  data: DailyTransactionPoint[];
  maxRevenue: number;
}) {
  const W = 700;
  const H = 240;
  const padX = 40;
  const padY = 30;
  if (data.length === 0) return null;
  const xStep = data.length > 1 ? (W - padX * 2) / (data.length - 1) : 0;
  const yScale = (H - padY * 2) / maxRevenue;
  const points = data
    .map(
      (d, i) =>
        `${padX + i * xStep},${H - padY - d.total_revenue * yScale}`
    )
    .join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mt-4 h-60 w-full">
      <defs>
        <linearGradient id="rev-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 1, 2, 3].map((i) => (
        <line
          key={i}
          x1={padX}
          y1={padY + (i * (H - padY * 2)) / 3}
          x2={W - padX}
          y2={padY + (i * (H - padY * 2)) / 3}
          stroke="#e2e8f0"
          strokeDasharray="2 4"
        />
      ))}
      <polygon
        points={`${padX},${H - padY} ${points} ${W - padX},${H - padY}`}
        fill="url(#rev-grad)"
      />
      <polyline
        points={points}
        fill="none"
        stroke="#6366f1"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {data.map((d, i) => (
        <text
          key={d.day}
          x={padX + i * xStep}
          y={H - 8}
          textAnchor="middle"
          fontSize="9"
          fill="#94a3b8"
        >
          {formatDate(d.day)}
        </text>
      ))}
    </svg>
  );
}

function TierDistributionList({
  data,
  total,
}: {
  data: TierDistributionPoint[];
  total: number;
}) {
  const colors = [
    "bg-amber-700",
    "bg-slate-400",
    "bg-amber-500",
    "bg-violet-500",
    "bg-indigo-500",
  ];
  return (
    <ul className="mt-4 space-y-2">
      {data.map((tier, idx) => {
        const percent = total > 0 ? (tier.member_count / total) * 100 : 0;
        return (
          <li key={tier.tier_id ?? `none-${idx}`} className="space-y-1">
            <div className="flex items-center justify-between text-[12px]">
              <span className="flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    colors[idx % colors.length]
                  }`}
                />
                <span className="font-medium text-slate-700">
                  {tier.tier_name}
                </span>
              </span>
              <span className="font-bold text-slate-800">
                {tier.member_count} · {percent.toFixed(0)}%
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full ${colors[idx % colors.length]}`}
                style={{ width: `${percent}%` }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
