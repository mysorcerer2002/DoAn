import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Gift,
  QrCode,
  ShieldCheck,
  Sparkles,
  Store,
  TrendingUp,
  Users,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      {/* Sticky navigation */}
      <nav className="sticky top-0 z-40 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-indigo to-brand-violet font-headline text-lg font-bold text-white shadow-md">
              L
            </div>
            <span className="font-headline text-[16px] font-bold text-slate-800">
              Loyalty Platform
            </span>
          </Link>
          <div className="hidden items-center gap-6 md:flex">
            <a
              href="#features"
              className="text-[13px] font-medium text-slate-600 hover:text-brand-indigo"
            >
              Tính năng
            </a>
            <a
              href="#stats"
              className="text-[13px] font-medium text-slate-600 hover:text-brand-indigo"
            >
              Thống kê
            </a>
            <a
              href="#for-who"
              className="text-[13px] font-medium text-slate-600 hover:text-brand-indigo"
            >
              Đối tượng
            </a>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-[13px] font-bold text-slate-700 hover:border-brand-indigo hover:text-brand-indigo"
            >
              Đăng nhập
            </Link>
            <Link
              href="/register"
              className="rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-4 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 hover:opacity-95"
            >
              Đăng ký miễn phí
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-950 via-brand-indigo to-brand-violet">
        <div className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-brand-orange/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -left-20 h-80 w-80 rounded-full bg-white/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-4 py-16 md:px-8 md:py-24 lg:grid-cols-2">
          {/* Left: copy */}
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-[11px] font-bold text-white backdrop-blur">
              <Sparkles className="h-3 w-3 text-brand-orange" />
              ĐỒ ÁN THỰC TẬP TỐT NGHIỆP 2026
            </div>
            <h1 className="mt-6 font-headline text-[42px] font-bold leading-tight text-white md:text-[56px]">
              Nền tảng tích điểm{" "}
              <span className="text-brand-orange">thông minh</span> cho cửa hàng
              Việt Nam
            </h1>
            <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-indigo-100/90 lg:mx-0">
              Multi-tenant loyalty platform giúp SME quản lý thành viên, phát
              voucher, theo dõi doanh thu — tất cả qua một tài khoản.
            </p>
            <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row lg:items-start">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-6 py-4 font-headline text-[15px] font-bold text-brand-indigo shadow-xl transition-transform hover:scale-[1.02] sm:w-auto"
              >
                Bắt đầu miễn phí
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/login"
                className="inline-flex w-full items-center justify-center rounded-2xl border border-white/30 bg-white/10 px-6 py-4 font-headline text-[15px] font-bold text-white backdrop-blur hover:bg-white/20 sm:w-auto"
              >
                Đã có tài khoản? Đăng nhập
              </Link>
            </div>
            <p className="mt-5 text-[12px] text-white/60">
              ⚡ +100 điểm chào mừng khi đăng ký · Không cần thẻ tín dụng
            </p>
          </div>

          {/* Right: floating glass cards */}
          <div className="relative hidden h-[520px] lg:block">
            {/* Dashboard analytics card */}
            <div className="absolute left-0 top-4 w-72 rounded-2xl border border-white/20 bg-white/95 p-5 shadow-2xl backdrop-blur">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-brand-indigo">
                    <BarChart3 className="h-4 w-4" />
                  </div>
                  <span className="font-headline text-[12px] font-bold text-slate-800">
                    Doanh thu 7 ngày
                  </span>
                </div>
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-600">
                  +24.5%
                </span>
              </div>
              <p className="mt-3 font-headline text-[28px] font-bold text-slate-800">
                45.6M ₫
              </p>
              <div className="mt-3 flex h-16 items-end justify-between gap-1">
                {[40, 55, 38, 72, 90, 65, 85].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-t bg-gradient-to-t from-brand-indigo to-brand-violet"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>

            {/* Voucher card */}
            <div className="absolute right-0 top-32 w-64 -rotate-3 rounded-2xl border-l-4 border-brand-orange bg-white p-4 shadow-2xl">
              <span className="absolute -top-1 left-20 h-3 w-3 rounded-full border border-slate-100 bg-[#f8fafc]" />
              <span className="absolute -bottom-1 left-20 h-3 w-3 rounded-full border border-slate-100 bg-[#f8fafc]" />
              <div className="flex items-center gap-2">
                <Gift className="h-4 w-4 text-brand-orange" />
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Voucher
                </span>
              </div>
              <p className="mt-2 text-[13px] font-bold text-slate-800">
                Giảm 20% Coffee
              </p>
              <p className="font-headline text-[32px] font-bold leading-none text-brand-orange">
                -20%
              </p>
              <p className="mt-1 text-[10px] text-slate-400">
                Hết hạn 20/04/2026
              </p>
            </div>

            {/* Member QR card */}
            <div className="absolute bottom-0 left-12 w-64 rotate-2 rounded-2xl border border-white/20 bg-gradient-to-br from-brand-indigo to-brand-violet p-5 text-white shadow-2xl">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-100">
                  Điểm tích lũy
                </span>
                <QrCode className="h-5 w-5 text-white/70" />
              </div>
              <p className="mt-2 font-headline text-[48px] font-bold leading-none text-brand-orange">
                2.450
              </p>
              <p className="mt-1 text-[11px] text-indigo-100">
                🥇 Hạng Vàng · 3 cửa hàng
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-7xl px-4 py-20 md:px-8">
        <div className="text-center">
          <p className="text-[12px] font-bold uppercase tracking-widest text-brand-indigo">
            Tính năng cốt lõi
          </p>
          <h2 className="mt-3 font-headline text-[32px] font-bold text-slate-800 md:text-[40px]">
            Tất cả trong một nền tảng
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-[15px] text-slate-500">
            Từ tích điểm qua QR đến phân tích doanh thu — Loyalty Platform cung
            cấp bộ công cụ đầy đủ cho SME Việt Nam.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          <FeatureCard
            number="01"
            icon={QrCode}
            title="Tích điểm bằng QR"
            desc="Khách quét mã cá nhân tại quầy, nhân viên bấm tạo giao dịch — tích điểm ngay lập tức. JWT QR token rotate mỗi 2 phút."
            color="indigo"
          />
          <FeatureCard
            number="02"
            icon={Gift}
            title="Đổi phần thưởng"
            desc="Kho quà tùy biến, stock management, auto voucher sinh nhật. Khách đổi quà ngay trong app, không cần bạc lẻ."
            color="orange"
          />
          <FeatureCard
            number="03"
            icon={TrendingUp}
            title="Báo cáo thời gian thực"
            desc="Dashboard doanh thu theo ngày, phân bố hạng thành viên, ROI chiến dịch. Xuất báo cáo PDF/Excel."
            color="violet"
          />
        </div>
      </section>

      {/* Stats strip */}
      <section
        id="stats"
        className="bg-slate-900 py-16 text-white md:py-20"
      >
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="grid grid-cols-2 gap-8 text-center md:grid-cols-4">
            <StatBig value="1000+" label="Cửa hàng tin dùng" />
            <StatBig value="50K+" label="Thành viên active" />
            <StatBig value="2M+" label="Điểm đã phát" />
            <StatBig value="99.9%" label="Uptime SLA" />
          </div>
        </div>
      </section>

      {/* Dual CTA */}
      <section id="for-who" className="mx-auto max-w-7xl px-4 py-20 md:px-8">
        <div className="text-center">
          <p className="text-[12px] font-bold uppercase tracking-widest text-brand-indigo">
            Phù hợp với bạn
          </p>
          <h2 className="mt-3 font-headline text-[32px] font-bold text-slate-800 md:text-[40px]">
            Hai trải nghiệm, một nền tảng
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Customer */}
          <article className="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-indigo to-indigo-800 p-8 text-white shadow-xl">
            <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
            <div className="relative z-10">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
                <Users className="h-7 w-7 text-white" />
              </div>
              <h3 className="mt-5 font-headline text-[24px] font-bold">
                Dành cho Khách hàng
              </h3>
              <p className="mt-2 text-[14px] text-indigo-100">
                Tích điểm đa cửa hàng, đổi voucher, theo dõi hạng thành viên
              </p>
              <ul className="mt-5 space-y-2">
                <CTALi>Tích điểm không cần thẻ vật lý</CTALi>
                <CTALi>Voucher sinh nhật tự động</CTALi>
                <CTALi>Lịch sử giao dịch đầy đủ</CTALi>
              </ul>
              <Link
                href="/register"
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 font-headline text-[13px] font-bold text-brand-indigo hover:scale-[1.02]"
              >
                Trở thành thành viên
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </article>

          {/* Merchant */}
          <article className="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-violet to-purple-900 p-8 text-white shadow-xl">
            <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-brand-orange/20 blur-2xl" />
            <div className="relative z-10">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
                <Store className="h-7 w-7 text-white" />
              </div>
              <h3 className="mt-5 font-headline text-[24px] font-bold">
                Dành cho Chủ cửa hàng
              </h3>
              <p className="mt-2 text-[14px] text-violet-100">
                Quản lý thành viên, phát voucher, xem báo cáo real-time
              </p>
              <ul className="mt-5 space-y-2">
                <CTALi>POS tích điểm nhanh qua QR</CTALi>
                <CTALi>Chiến dịch khuyến mãi tự động</CTALi>
                <CTALi>Phân quyền staff + báo cáo ROI</CTALi>
              </ul>
              <Link
                href="/register"
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-brand-orange px-5 py-3 font-headline text-[13px] font-bold text-white hover:scale-[1.02]"
              >
                Đăng ký cửa hàng
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </article>
        </div>
      </section>

      {/* Security note */}
      <section className="mx-auto max-w-7xl px-4 pb-20 md:px-8">
        <div className="flex flex-col items-start gap-4 rounded-2xl border border-slate-200 bg-white p-6 md:flex-row md:items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <h3 className="font-headline text-[15px] font-bold text-slate-800">
              Bảo mật chuẩn enterprise
            </h3>
            <p className="mt-1 text-[12px] text-slate-500">
              JWT access/refresh token · bcrypt password · HTTPS qua Cloudflare
              Tunnel · Multi-tenant isolation · Rate limiting · Alembic
              migrations
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-white py-10">
        <div className="mx-auto max-w-7xl px-4 text-center md:px-8">
          <div className="flex items-center justify-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-indigo to-brand-violet font-headline text-sm font-bold text-white">
              L
            </div>
            <span className="font-headline text-[14px] font-bold text-slate-800">
              Loyalty Platform
            </span>
          </div>
          <p className="mt-3 text-[11px] text-slate-400">
            © 2026 Loyalty Platform — Đồ án thực tập tốt nghiệp · Multi-tenant
            loyalty cho SME Việt Nam
          </p>
        </div>
      </footer>
    </div>
  );
}

const FEATURE_COLORS = {
  indigo: "bg-indigo-50 text-brand-indigo",
  orange: "bg-orange-50 text-brand-orange",
  violet: "bg-violet-50 text-brand-violet",
} as const;

function FeatureCard({
  number,
  icon: Icon,
  title,
  desc,
  color,
}: {
  number: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  color: keyof typeof FEATURE_COLORS;
}) {
  return (
    <article className="group relative overflow-hidden rounded-3xl border border-slate-100 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
      <div className="absolute right-6 top-4 font-headline text-[72px] font-bold leading-none text-slate-100 transition-colors group-hover:text-slate-200">
        {number}
      </div>
      <div
        className={`relative z-10 flex h-14 w-14 items-center justify-center rounded-2xl ${FEATURE_COLORS[color]}`}
      >
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="relative z-10 mt-5 font-headline text-[20px] font-bold text-slate-800">
        {title}
      </h3>
      <p className="relative z-10 mt-3 text-[14px] leading-relaxed text-slate-500">
        {desc}
      </p>
    </article>
  );
}

function StatBig({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="font-headline text-[40px] font-bold text-brand-orange md:text-[56px]">
        {value}
      </p>
      <p className="mt-1 text-[12px] font-medium text-slate-300 md:text-[14px]">
        {label}
      </p>
    </div>
  );
}

function CTALi({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-2 text-[13px] text-white/90">
      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
      {children}
    </li>
  );
}
