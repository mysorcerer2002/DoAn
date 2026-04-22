import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Gift,
  QrCode,
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

        <div className="relative mx-auto max-w-3xl px-4 py-20 text-center md:px-8 md:py-28">
          <h1 className="font-headline text-[40px] font-bold leading-tight text-white md:text-[54px]">
            Nền tảng tích điểm{" "}
            <span className="text-brand-orange">thành viên</span> cho cửa hàng
            Việt Nam
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-[16px] leading-relaxed text-indigo-100/90">
            Giúp chủ cửa hàng quản lý khách hàng thân thiết, phát phiếu mua
            hàng và theo dõi doanh thu — tất cả trong một tài khoản.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
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
            Miễn phí đăng ký · Không cần khai báo thẻ
          </p>
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
            desc="Khách đưa mã cá nhân tại quầy, nhân viên quét và tạo giao dịch — điểm được cộng ngay vào tài khoản khách."
            color="indigo"
          />
          <FeatureCard
            number="02"
            icon={Gift}
            title="Đổi phần thưởng"
            desc="Chủ cửa hàng tự tạo kho quà, tặng phiếu mua hàng sinh nhật tự động. Khách đổi quà ngay trong ứng dụng."
            color="orange"
          />
          <FeatureCard
            number="03"
            icon={TrendingUp}
            title="Báo cáo doanh thu"
            desc="Xem doanh thu theo ngày, phân bố hạng thành viên và hiệu quả từng chiến dịch khuyến mãi."
            color="violet"
          />
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
                Tích điểm tại nhiều cửa hàng, đổi phiếu mua hàng, theo dõi
                hạng thành viên
              </p>
              <ul className="mt-5 space-y-2">
                <CTALi>Tích điểm không cần thẻ cứng</CTALi>
                <CTALi>Phiếu mua hàng sinh nhật tự động</CTALi>
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
                Quản lý thành viên, phát phiếu mua hàng, xem báo cáo doanh
                thu ngay trong ngày
              </p>
              <ul className="mt-5 space-y-2">
                <CTALi>Tích điểm nhanh bằng QR</CTALi>
                <CTALi>Chiến dịch khuyến mãi tự động</CTALi>
                <CTALi>Phân quyền nhân viên · báo cáo chi tiết</CTALi>
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

      <footer className="mt-10 border-t border-slate-200 bg-white py-10">
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
            © 2026 Loyalty Platform — Nền tảng tích điểm thành viên cho cửa
            hàng Việt Nam
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

function CTALi({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-2 text-[13px] text-white/90">
      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
      {children}
    </li>
  );
}
