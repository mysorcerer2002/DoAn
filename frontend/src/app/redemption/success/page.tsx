import { ArrowLeft, Check, Clock, Download, MapPin, Share2 } from "lucide-react";
import Link from "next/link";

export default function RedemptionSuccessPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-brand-indigo to-brand-violet font-body">
      {/* Decorative confetti dots */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[10%] top-[15%] h-2 w-2 rounded-full bg-white/40" />
        <div className="absolute left-[80%] top-[10%] h-3 w-3 rounded-full bg-orange-300/50" />
        <div className="absolute left-[20%] top-[40%] h-1.5 w-1.5 rounded-full bg-white/50" />
        <div className="absolute left-[70%] top-[50%] h-2 w-2 rounded-full bg-orange-300/40" />
        <div className="absolute left-[85%] top-[80%] h-2.5 w-2.5 rounded-full bg-white/30" />
        <div className="absolute left-[15%] top-[85%] h-2 w-2 rounded-full bg-orange-300/40" />
      </div>

      <header className="relative z-10 flex h-16 items-center justify-between px-4">
        <Link
          href="/member"
          className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/10"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/10"
          aria-label="Chia sẻ"
        >
          <Share2 className="h-6 w-6" />
        </button>
      </header>

      <main className="relative z-10 mx-auto max-w-md space-y-6 px-6 pb-12">
        {/* Success icon */}
        <div className="flex flex-col items-center pt-4">
          <div className="relative">
            <div className="absolute inset-0 -m-2 rounded-full bg-white/20 blur-xl" />
            <div className="relative flex h-28 w-28 items-center justify-center rounded-full bg-white shadow-2xl">
              <Check
                className="h-14 w-14 text-brand-indigo"
                strokeWidth={3.5}
              />
            </div>
          </div>
          <h1 className="mt-6 text-center font-headline text-[26px] font-bold text-white">
            Đổi quà thành công!
          </h1>
          <p className="mt-2 max-w-xs text-center text-[14px] text-white/80">
            Hãy đưa mã QR cho nhân viên để nhận quà
          </p>
        </div>

        {/* Reward card */}
        <article className="rounded-3xl bg-white p-6 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-5xl">
              ☕
            </div>
            <div className="flex-1">
              <h2 className="font-headline text-[18px] font-bold text-slate-800">
                Cafe Latte size M Free
              </h2>
              <p className="mt-1 flex items-center gap-1 text-[12px] text-slate-400">
                <MapPin className="h-3 w-3" />
                Cafe Cộng - Bà Triệu
              </p>
            </div>
          </div>

          <div className="my-4 border-t border-dashed border-slate-200" />

          <div className="space-y-2">
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-slate-500">Số điểm đã dùng</span>
              <span className="font-headline font-bold text-brand-orange">
                150 điểm
              </span>
            </div>
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-slate-500">Mã đổi quà</span>
              <span className="font-mono text-[12px] font-bold text-slate-800">
                RDM-A8K9-2026
              </span>
            </div>
          </div>

          {/* QR placeholder */}
          <div className="my-5 flex items-center justify-center">
            <div className="relative h-48 w-48 rounded-2xl border-4 border-slate-100 bg-white p-3 shadow-inner">
              <div
                className="h-full w-full bg-slate-800"
                style={{
                  backgroundImage:
                    "repeating-linear-gradient(0deg, #1e293b, #1e293b 6px, #fff 6px, #fff 10px), repeating-linear-gradient(90deg, transparent, transparent 6px, #1e293b 6px, #1e293b 10px)",
                  backgroundBlendMode: "difference",
                }}
              />
              <div className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-brand-indigo text-xl font-bold text-white shadow-lg">
                L
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-1 rounded-lg bg-amber-50 px-3 py-2">
            <Clock className="h-4 w-4 text-amber-600" />
            <span className="text-[12px] font-medium text-amber-700">
              Có hiệu lực trong 24 giờ
            </span>
          </div>
        </article>

        <div className="space-y-3">
          <button
            type="button"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-white py-4 font-headline font-bold text-brand-indigo shadow-lg active:scale-[0.98]"
          >
            <Download className="h-5 w-5" />
            Lưu ảnh QR
          </button>
          <Link
            href="/member/rewards"
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-white/40 py-4 font-medium text-white transition-colors hover:bg-white/10"
          >
            Xem phần thưởng đã đổi
          </Link>
        </div>
      </main>
    </div>
  );
}
