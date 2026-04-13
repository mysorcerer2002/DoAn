import {
  Activity,
  Calendar,
  Coins,
  CreditCard,
  Download,
  Plus,
  Store,
  Ticket,
  TrendingUp,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";
import { StatCard } from "@/components/ui/stat-card";

const topMerchants = [
  { name: "Cafe Cộng", revenue: "45M ₫", percent: 100, emoji: "☕" },
  { name: "BBQ Hàn Quốc", revenue: "38M ₫", percent: 84, emoji: "🍜" },
  { name: "Highland Coffee", revenue: "32M ₫", percent: 71, emoji: "☕" },
  { name: "Pizza Hut", revenue: "28M ₫", percent: 62, emoji: "🍕" },
  { name: "Trà sữa Toko", revenue: "24M ₫", percent: 53, emoji: "🥤" },
  { name: "Coolmate Pop-up", revenue: "20M ₫", percent: 44, emoji: "🛍️" },
  { name: "Cocoon", revenue: "18M ₫", percent: 40, emoji: "💄" },
  { name: "Bánh mì 25", revenue: "15M ₫", percent: 33, emoji: "🥖" },
  { name: "Phở Thìn", revenue: "12M ₫", percent: 27, emoji: "🍲" },
  { name: "Chè Bốn Mùa", revenue: "10M ₫", percent: 22, emoji: "🍧" },
];

const categoryDistribution = [
  { name: "Cafe & Đồ uống", percent: 35, color: "#6366f1" },
  { name: "Nhà hàng", percent: 25, color: "#8b5cf6" },
  { name: "Bán lẻ", percent: 20, color: "#fb923c" },
  { name: "Mỹ phẩm", percent: 10, color: "#ec4899" },
  { name: "Khác", percent: 10, color: "#94a3b8" },
];

const activities = [
  {
    id: "a1",
    icon: UserCheck,
    title: "Phê duyệt Cafe Cộng",
    time: "5 phút trước",
    color: "emerald",
  },
  {
    id: "a2",
    icon: Plus,
    title: "Trà sữa Toko đăng ký",
    time: "1 giờ trước",
    color: "indigo",
  },
  {
    id: "a3",
    icon: XCircle,
    title: "Từ chối Shop ABC",
    time: "2 giờ trước",
    color: "red",
  },
  {
    id: "a4",
    icon: Download,
    title: "Xuất báo cáo tháng 3",
    time: "1 ngày trước",
    color: "slate",
  },
  {
    id: "a5",
    icon: Users,
    title: "Tạo admin mới",
    time: "2 ngày trước",
    color: "indigo",
  },
];

const provinces = [
  { name: "Hà Nội", count: 45, x: 50, y: 25 },
  { name: "TP.HCM", count: 60, x: 55, y: 80 },
  { name: "Đà Nẵng", count: 25, x: 60, y: 50 },
  { name: "Hải Phòng", count: 12, x: 55, y: 22 },
  { name: "Cần Thơ", count: 8, x: 45, y: 88 },
  { name: "Nha Trang", count: 6, x: 65, y: 65 },
];

export default function AdminStatsPage() {
  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Hệ thống / Thống kê</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Thống kê hệ thống
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-[13px] font-medium text-slate-700 hover:border-brand-indigo"
          >
            <Calendar className="h-4 w-4 text-brand-indigo" />
            Tháng 4/2026
          </button>
          <select
            aria-label="Phạm vi thống kê"
            className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-[13px]"
          >
            <option>Phạm vi: Toàn hệ thống</option>
            <option>Theo vùng miền</option>
            <option>Theo danh mục</option>
          </select>
          <button
            type="button"
            className="flex items-center gap-2 rounded-xl border border-brand-indigo bg-white px-4 py-2.5 text-[13px] font-bold text-brand-indigo hover:bg-brand-indigo/5"
          >
            <Download className="h-4 w-4" />
            Xuất báo cáo
          </button>
        </div>
      </header>

      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          icon={Store}
          label="Tổng đối tác"
          value="156"
          tone="indigo"
          trend={{ value: "+12 tháng này", direction: "up" }}
        />
        <StatCard
          icon={Users}
          label="Tổng thành viên"
          value="12.450"
          tone="indigo"
          trend={{ value: "+850 tháng này", direction: "up" }}
        />
        <StatCard
          icon={CreditCard}
          label="Tổng giao dịch"
          value="45.230"
          tone="orange"
          trend={{ value: "+8.5%", direction: "up" }}
        />
        <StatCard
          icon={Coins}
          label="Điểm phát hành"
          value="2.5M"
          tone="orange"
          highlightValue
          trend={{ value: "+12.3%", direction: "up" }}
        />
        <StatCard
          icon={Ticket}
          label="Voucher đã đổi"
          value="8.234"
          tone="orange"
          trend={{ value: "+5.8%", direction: "up" }}
        />
        <StatCard
          icon={TrendingUp}
          label="Doanh thu nền tảng"
          value="245M ₫"
          tone="indigo"
          trend={{ value: "+15.2%", direction: "up" }}
        />
      </section>

      <section className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-2">
          <header>
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Tăng trưởng đối tác & thành viên
            </h2>
            <p className="text-[12px] text-slate-400">
              12 tháng qua · So sánh đối tác mới và thành viên mới
            </p>
          </header>
          <GrowthChart />
          <div className="mt-3 flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-brand-indigo" />
              Đối tác mới
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-brand-orange" />
              Thành viên mới
            </span>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Top 10 đối tác doanh thu
          </h2>
          <ul className="mt-4 space-y-2.5">
            {topMerchants.map((m) => (
              <li key={m.name} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 font-medium text-slate-700">
                    <span className="text-base">{m.emoji}</span>
                    {m.name}
                  </span>
                  <span className="font-bold text-slate-800">{m.revenue}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-indigo to-brand-violet"
                    style={{ width: `${m.percent}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Phân bố theo danh mục
          </h2>
          <div className="mt-4 flex items-center gap-6">
            <CategoryDonut data={categoryDistribution} />
            <ul className="flex-1 space-y-2.5">
              {categoryDistribution.map((cat) => (
                <li
                  key={cat.name}
                  className="flex items-center justify-between text-[12px]"
                >
                  <span className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: cat.color }}
                    />
                    <span className="font-medium text-slate-700">
                      {cat.name}
                    </span>
                  </span>
                  <span className="font-bold text-slate-800">{cat.percent}%</span>
                </li>
              ))}
            </ul>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Hoạt động gần đây
          </h2>
          <ol className="mt-4 space-y-3">
            {activities.map((a, idx) => (
              <li key={a.id} className="flex items-start gap-3">
                <div className="relative">
                  <div
                    className={
                      a.color === "emerald"
                        ? "flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-emerald-600"
                        : a.color === "red"
                        ? "flex h-8 w-8 items-center justify-center rounded-full bg-red-50 text-red-600"
                        : a.color === "slate"
                        ? "flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-600"
                        : "flex h-8 w-8 items-center justify-center rounded-full bg-indigo-50 text-brand-indigo"
                    }
                  >
                    <a.icon className="h-4 w-4" />
                  </div>
                  {idx < activities.length - 1 && (
                    <div className="absolute left-1/2 top-8 h-3 w-px -translate-x-1/2 bg-slate-200" />
                  )}
                </div>
                <div className="flex-1 pt-1">
                  <p className="text-[13px] font-medium text-slate-800">
                    {a.title}
                  </p>
                  <p className="text-[11px] text-slate-400">{a.time}</p>
                </div>
              </li>
            ))}
          </ol>
        </article>
      </section>

      <section className="mt-5 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <header className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-brand-indigo" />
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Phân bố đối tác theo địa lý
          </h2>
        </header>
        <p className="text-[12px] text-slate-400">
          Heat map các tỉnh thành có đối tác đăng ký
        </p>
        <div className="mt-4 flex items-center gap-6">
          <VietnamMap provinces={provinces} />
          <ul className="flex-1 space-y-2">
            {[...provinces]
              .sort((a, b) => b.count - a.count)
              .map((p) => (
                <li
                  key={p.name}
                  className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-[12px]"
                >
                  <span className="font-medium text-slate-700">{p.name}</span>
                  <span className="rounded-full bg-brand-indigo px-2 py-0.5 text-[11px] font-bold text-white">
                    {p.count} đối tác
                  </span>
                </li>
              ))}
          </ul>
        </div>
      </section>
    </main>
  );
}

function GrowthChart() {
  // 12 month mock data
  const months = [
    "T5",
    "T6",
    "T7",
    "T8",
    "T9",
    "T10",
    "T11",
    "T12",
    "T1",
    "T2",
    "T3",
    "T4",
  ];
  const merchants = [80, 90, 95, 105, 115, 125, 130, 138, 142, 148, 152, 156];
  const members = [
    5400, 6100, 6800, 7500, 8200, 9000, 9800, 10500, 11200, 11800, 12200, 12450,
  ];

  const w = 700;
  const h = 240;
  const padX = 40;
  const padY = 30;
  const xStep = (w - padX * 2) / (months.length - 1);

  const maxM = Math.max(...merchants);
  const maxU = Math.max(...members);
  const yScaleM = (h - padY * 2) / maxM;
  const yScaleU = (h - padY * 2) / maxU;

  const pointsM = merchants
    .map((v, i) => `${padX + i * xStep},${h - padY - v * yScaleM}`)
    .join(" ");
  const pointsU = members
    .map((v, i) => `${padX + i * xStep},${h - padY - v * yScaleU}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="mt-4 h-60 w-full">
      <defs>
        <linearGradient id="grad-m" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 1, 2, 3, 4].map((i) => (
        <line
          key={i}
          x1={padX}
          y1={padY + (i * (h - padY * 2)) / 4}
          x2={w - padX}
          y2={padY + (i * (h - padY * 2)) / 4}
          stroke="#e2e8f0"
          strokeDasharray="2 4"
        />
      ))}
      <polygon
        points={`${padX},${h - padY} ${pointsM} ${w - padX},${h - padY}`}
        fill="url(#grad-m)"
      />
      <polyline
        points={pointsM}
        fill="none"
        stroke="#6366f1"
        strokeWidth="2.5"
      />
      <polyline
        points={pointsU}
        fill="none"
        stroke="#fb923c"
        strokeWidth="2.5"
        strokeDasharray="4 4"
      />
      {months.map((m, i) => (
        <text
          key={m}
          x={padX + i * xStep}
          y={h - 8}
          textAnchor="middle"
          fontSize="9"
          fill="#94a3b8"
        >
          {m}
        </text>
      ))}
    </svg>
  );
}

function CategoryDonut({
  data,
}: {
  data: { name: string; percent: number; color: string }[];
}) {
  const radius = 50;
  const stroke = 18;
  const cx = 70;
  const cy = 70;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <svg viewBox="0 0 140 140" className="h-36 w-36">
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill="none"
        stroke="#f1f5f9"
        strokeWidth={stroke}
      />
      {data.map((slice) => {
        const length = (slice.percent / 100) * circumference;
        const dasharray = `${length} ${circumference - length}`;
        const dashoffset = -offset;
        offset += length;
        return (
          <circle
            key={slice.name}
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke={slice.color}
            strokeWidth={stroke}
            strokeDasharray={dasharray}
            strokeDashoffset={dashoffset}
            transform={`rotate(-90 ${cx} ${cy})`}
          />
        );
      })}
      <text
        x={cx}
        y={cy - 4}
        textAnchor="middle"
        fontSize="22"
        fontWeight="700"
        fill="#1e293b"
      >
        156
      </text>
      <text
        x={cx}
        y={cy + 14}
        textAnchor="middle"
        fontSize="9"
        fill="#94a3b8"
      >
        Đối tác
      </text>
    </svg>
  );
}

function VietnamMap({
  provinces,
}: {
  provinces: { name: string; count: number; x: number; y: number }[];
}) {
  return (
    <div className="relative h-72 w-56 shrink-0 rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50">
      <svg viewBox="0 0 100 100" className="h-full w-full">
        {/* Stylized Vietnam outline */}
        <path
          d="M 50 5 Q 55 15 52 25 Q 50 35 55 45 Q 60 55 55 65 Q 50 75 55 85 Q 60 92 50 95 Q 40 92 45 80 Q 50 68 45 58 Q 40 48 45 38 Q 50 28 45 18 Q 47 10 50 5 Z"
          fill="rgba(99,102,241,0.15)"
          stroke="#6366f1"
          strokeWidth="0.5"
        />
        {provinces.map((p) => (
          <g key={p.name}>
            <circle
              cx={p.x}
              cy={p.y}
              r={Math.sqrt(p.count) / 1.2}
              fill="#fb923c"
              opacity="0.8"
            />
            <circle
              cx={p.x}
              cy={p.y}
              r={Math.sqrt(p.count) / 1.2}
              fill="none"
              stroke="#fb923c"
              strokeWidth="0.3"
            >
              <animate
                attributeName="r"
                from={Math.sqrt(p.count) / 1.2}
                to={Math.sqrt(p.count) / 1.2 + 3}
                dur="2s"
                repeatCount="indefinite"
              />
              <animate
                attributeName="opacity"
                from="0.6"
                to="0"
                dur="2s"
                repeatCount="indefinite"
              />
            </circle>
          </g>
        ))}
      </svg>
    </div>
  );
}
