import Link from "next/link";
import { ArrowRight, Gift, QrCode, Sparkles, TrendingUp } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <div className="relative mx-auto max-w-md overflow-hidden">
        <section className="relative flex min-h-[70vh] flex-col items-center justify-center bg-gradient-to-br from-brand-indigo via-brand-violet to-indigo-900 px-6 pt-16 pb-20 text-center">
          <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-brand-orange/20 blur-3xl" />
          <div className="pointer-events-none absolute -left-16 bottom-10 h-60 w-60 rounded-full bg-white/10 blur-3xl" />

          <div className="relative mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-white shadow-2xl">
            <span className="font-headline text-5xl font-bold text-brand-indigo">
              L
            </span>
            <div className="absolute -right-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full bg-brand-orange shadow-lg">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
          </div>

          <h1 className="font-headline text-[40px] font-bold leading-tight text-white">
            Loyalty Platform
          </h1>
          <p className="mt-3 max-w-xs text-[15px] leading-relaxed text-white/85">
            Nền tảng tích điểm & đổi quà cho khách hàng thân thiết của các SME
            Việt Nam
          </p>

          <div className="relative mt-10 w-full max-w-xs space-y-3">
            <Link
              href="/register"
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-white py-4 font-headline text-[15px] font-bold text-brand-indigo shadow-xl transition-transform active:scale-[0.98]"
            >
              Đăng ký miễn phí
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/login"
              className="flex w-full items-center justify-center rounded-2xl border border-white/30 bg-white/10 py-4 font-headline text-[15px] font-bold text-white backdrop-blur transition-colors hover:bg-white/20"
            >
              Đã có tài khoản? Đăng nhập
            </Link>
          </div>

          <p className="relative mt-6 text-[12px] text-white/60">
            +100 điểm chào mừng cho thành viên mới
          </p>
        </section>

        <section className="-mt-10 px-5 pb-16">
          <div className="grid grid-cols-1 gap-3">
            <FeatureCard
              icon={QrCode}
              title="Quét QR tích điểm"
              desc="Cho nhân viên quét mã QR cá nhân tại quầy — nhận điểm ngay tức thì"
              color="indigo"
            />
            <FeatureCard
              icon={Gift}
              title="Đổi phần thưởng hấp dẫn"
              desc="Dùng điểm đổi voucher, cafe miễn phí hoặc ưu đãi độc quyền"
              color="orange"
            />
            <FeatureCard
              icon={TrendingUp}
              title="Theo dõi hạng thành viên"
              desc="Đồng → Bạc → Vàng → Bạch Kim. Càng chi tiêu, càng nhiều ưu đãi"
              color="violet"
            />
          </div>

          <div className="mt-10 rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50 p-5 text-center">
            <p className="font-headline text-[13px] font-semibold text-brand-indigo">
              Dành cho chủ cửa hàng
            </p>
            <p className="mt-2 text-[12px] text-slate-600">
              Quản lý thành viên, tạo chiến dịch khuyến mãi, xem báo cáo doanh
              thu — tất cả trong một nền tảng.
            </p>
            <Link
              href="/login"
              className="mt-4 inline-flex items-center gap-1 font-headline text-[13px] font-bold text-brand-indigo hover:underline"
            >
              Vào trang Merchant
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        <footer className="px-8 pb-10 text-center">
          <p className="text-[10px] leading-relaxed text-slate-400">
            © 2026 Loyalty Platform — Đồ án thực tập tốt nghiệp
          </p>
        </footer>
      </div>
    </div>
  );
}

const COLOR_MAP = {
  indigo: "bg-indigo-50 text-brand-indigo",
  orange: "bg-orange-50 text-brand-orange",
  violet: "bg-violet-50 text-brand-violet",
} as const;

function FeatureCard({
  icon: Icon,
  title,
  desc,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  color: keyof typeof COLOR_MAP;
}) {
  return (
    <article className="flex items-start gap-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div
        className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl ${COLOR_MAP[color]}`}
      >
        <Icon className="h-6 w-6" />
      </div>
      <div className="flex-1">
        <h3 className="font-headline text-[15px] font-bold text-slate-800">
          {title}
        </h3>
        <p className="mt-1 text-[12px] leading-relaxed text-slate-500">
          {desc}
        </p>
      </div>
    </article>
  );
}
