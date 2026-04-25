"use client";

import {
  Calendar,
  Download,
  Loader2,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { useDashboard } from "@/lib/hooks/use-partner";
import type {
  DailyTransactionPoint,
  TierDistributionPoint,
} from "@/types/partner";

function formatVnd(n: number): string {
  return n.toLocaleString("vi-VN") + " ₫";
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

/** Tính % thay đổi giữa nửa sau và nửa đầu của chuỗi số. */
function periodTrend(values: number[]): number | null {
  if (values.length < 4) return null;
  const half = Math.floor(values.length / 2);
  const first = values.slice(0, half).reduce((a, b) => a + b, 0);
  const second = values.slice(half).reduce((a, b) => a + b, 0);
  if (first === 0) return second > 0 ? 100 : null;
  return ((second - first) / first) * 100;
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

  // Compute trends từ daily_transactions (nửa cuối vs nửa đầu period)
  const revenueTrend = periodTrend(
    data.daily_transactions.map((d) => d.total_revenue)
  );
  const txnTrend = periodTrend(
    data.daily_transactions.map((d) => d.transaction_count)
  );
  const pointsTrend = periodTrend(
    data.daily_transactions.map((d) => d.total_points_earned)
  );

  const avgRevenuePerDay =
    data.daily_transactions.length > 0
      ? data.total_revenue / data.daily_transactions.length
      : 0;
  const revenueProgress = Math.min(
    100,
    (avgRevenuePerDay / Math.max(1, maxRevenue)) * 100
  );

  const totalPointsIssued = data.daily_transactions.reduce(
    (sum, d) => sum + d.total_points_earned,
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
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 hover:opacity-95"
          >
            <Download className="h-4 w-4" />
            Xuất báo cáo
          </button>
        </div>
      </header>

      {/* KPI cards với trend badge + progress bar */}
      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Doanh thu"
          value={formatVnd(data.total_revenue)}
          trend={revenueTrend}
          progress={revenueProgress}
          progressColor="bg-brand-indigo"
        />
        <KpiCard
          label="Giao dịch"
          value={data.transaction_count.toLocaleString("vi-VN")}
          trend={txnTrend}
          progress={Math.min(100, (data.transaction_count / 1000) * 100)}
          progressColor="bg-brand-violet"
        />
        <KpiCard
          label="Thành viên"
          value={totalMembers.toLocaleString("vi-VN")}
          trend={null}
          progress={Math.min(100, (totalMembers / 500) * 100)}
          progressColor="bg-brand-indigo"
        />
        <KpiCard
          label="Điểm phát hành"
          value={totalPointsIssued.toLocaleString("vi-VN")}
          trend={pointsTrend}
          progress={Math.min(100, (totalPointsIssued / 20000) * 100)}
          progressColor="bg-brand-orange"
          highlight
        />
      </section>

      {/* Charts row: Line chart (2/3) + Donut tier (1/3) */}
      <section className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-2">
          <header className="flex items-center justify-between">
            <div>
              <h2 className="font-headline text-[18px] font-bold text-slate-800">
                Doanh thu theo ngày
              </h2>
              <p className="text-[12px] text-slate-400">
                {data.daily_transactions.length} ngày
              </p>
            </div>
            <div className="hidden items-center gap-4 md:flex">
              <LegendDot color="bg-brand-indigo" label="Doanh thu" />
              <LegendDot color="bg-brand-orange" label="Điểm tích" />
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
          <TierDonutChart data={data.tier_distribution} total={totalMembers} />
        </article>
      </section>

    </main>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2 text-[11px] text-slate-500">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      {label}
    </div>
  );
}

function KpiCard({
  label,
  value,
  trend,
  progress,
  progressColor,
  highlight = false,
}: {
  label: string;
  value: string;
  trend: number | null;
  progress: number;
  progressColor: string;
  highlight?: boolean;
}) {
  const trendPositive = trend != null && trend >= 0;
  return (
    <article className="flex flex-col justify-between rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <span className="text-[13px] font-medium text-slate-500">{label}</span>
        {trend != null && (
          <span
            className={
              trendPositive
                ? "flex items-center gap-0.5 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-600"
                : "flex items-center gap-0.5 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-600"
            }
          >
            {trendPositive ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {trendPositive ? "+" : ""}
            {trend.toFixed(1)}%
          </span>
        )}
      </div>
      <div
        className={
          highlight
            ? "mt-3 font-headline text-[24px] font-bold leading-tight text-brand-orange"
            : "mt-3 font-headline text-[24px] font-bold leading-tight text-slate-800"
        }
      >
        {value}
      </div>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${progressColor}`}
          style={{ width: `${progress}%` }}
        />
      </div>
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
      (d, i) => `${padX + i * xStep},${H - padY - d.total_revenue * yScale}`
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
        <circle
          key={`dot-${d.day}`}
          cx={padX + i * xStep}
          cy={H - padY - d.total_revenue * yScale}
          r="3"
          fill="#fff"
          stroke="#6366f1"
          strokeWidth="2"
        />
      ))}
      {data
        .filter((_, i) => i % Math.max(1, Math.floor(data.length / 8)) === 0)
        .map((d, idx) => {
          const realIdx = data.indexOf(d);
          return (
            <text
              key={`x-${d.day}-${idx}`}
              x={padX + realIdx * xStep}
              y={H - 8}
              textAnchor="middle"
              fontSize="9"
              fill="#94a3b8"
            >
              {formatDate(d.day)}
            </text>
          );
        })}
    </svg>
  );
}

const TIER_COLORS = [
  "#B45309", // Bronze — amber-700
  "#94A3B8", // Silver — slate-400
  "#F59E0B", // Gold — amber-500
  "#8B5CF6", // Platinum — violet-500
  "#6366F1", // Diamond — indigo-500
];

function TierDonutChart({
  data,
  total,
}: {
  data: TierDistributionPoint[];
  total: number;
}) {
  const size = 180;
  const stroke = 20;
  const radius = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * radius;

  if (total === 0) {
    return (
      <div className="mt-6 flex h-40 items-center justify-center text-[13px] text-slate-400">
        Chưa có thành viên nào
      </div>
    );
  }

  let accum = 0;
  const segments = data.map((tier, idx) => {
    const percent = tier.member_count / total;
    const offset = circumference * accum;
    const length = circumference * percent;
    accum += percent;
    return {
      idx,
      tier,
      percent,
      offset,
      length,
      color: TIER_COLORS[idx % TIER_COLORS.length],
    };
  });

  return (
    <div className="mt-6">
      <div className="relative mx-auto" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="-rotate-90"
          aria-label="Biểu đồ phân bố hạng thành viên"
        >
          <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth={stroke}
          />
          {segments.map((s) => (
            <circle
              key={s.idx}
              cx={cx}
              cy={cy}
              r={radius}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeDasharray={`${s.length} ${circumference - s.length}`}
              strokeDashoffset={-s.offset}
              strokeLinecap="butt"
            />
          ))}
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-headline text-[28px] font-bold text-slate-800">
            {total}
          </span>
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Tổng
          </span>
        </div>
      </div>
      <ul className="mt-6 space-y-2.5">
        {segments.map((s) => (
          <li
            key={s.idx}
            className="flex items-center justify-between text-[13px]"
          >
            <span className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="text-slate-600">{s.tier.tier_name}</span>
            </span>
            <span className="font-bold text-slate-800">
              {s.tier.member_count} · {(s.percent * 100).toFixed(0)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
