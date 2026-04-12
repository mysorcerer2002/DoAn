import { ArrowLeft, Crown, Info, RefreshCw, Sun } from "lucide-react";
import Link from "next/link";

export default function MemberQrPage() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-gradient-to-br from-brand-indigo to-brand-violet font-body">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col px-5 pb-10">
        <header className="flex h-16 items-center justify-between">
          <Link
            href="/member"
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/10"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <h1 className="font-headline text-[18px] font-bold text-white">
            Mã QR của tôi
          </h1>
          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/10"
            aria-label="Tăng độ sáng"
          >
            <Sun className="h-6 w-6" />
          </button>
        </header>

        <section className="rounded-2xl border border-white/30 bg-white/15 p-4 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-white/40 bg-gradient-to-br from-indigo-200 to-violet-200 text-base font-bold text-indigo-700">
              MA
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h2 className="font-headline text-[16px] font-bold text-white">
                  Nguyễn Minh Anh
                </h2>
                <div className="flex items-center gap-0.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-1.5 py-0.5">
                  <Crown
                    className="h-2.5 w-2.5 text-white"
                    fill="white"
                  />
                </div>
              </div>
              <p className="text-[12px] text-white/70">•••• •• 8876</p>
            </div>
            <div className="text-right">
              <p className="font-headline text-[22px] font-bold text-brand-orange leading-none">
                2.450
              </p>
              <p className="text-[10px] text-white/80">điểm</p>
            </div>
          </div>
        </section>

        <section className="mt-8 flex flex-1 flex-col items-center justify-center">
          <div className="relative">
            <div className="absolute inset-0 -m-3 rounded-3xl bg-white/20 blur-2xl" />
            <div className="relative rounded-3xl bg-white p-6 shadow-2xl">
              <div className="relative flex h-64 w-64 items-center justify-center">
                <div
                  className="h-full w-full rounded-lg bg-slate-900"
                  style={{
                    backgroundImage:
                      "repeating-linear-gradient(0deg, #0f172a, #0f172a 8px, #fff 8px, #fff 12px), repeating-linear-gradient(90deg, transparent, transparent 8px, #0f172a 8px, #0f172a 12px)",
                    backgroundBlendMode: "difference",
                  }}
                />
                <div className="absolute left-1/2 top-1/2 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-brand-indigo text-2xl font-bold text-white shadow-lg">
                  L
                </div>
                {/* Corner finder squares */}
                <div className="absolute left-2 top-2 h-8 w-8 border-4 border-white" />
                <div className="absolute right-2 top-2 h-8 w-8 border-4 border-white" />
                <div className="absolute bottom-2 left-2 h-8 w-8 border-4 border-white" />
              </div>
              <p className="mt-3 text-center font-mono text-[11px] text-slate-400">
                LP-MA-2026-X8K9
              </p>
            </div>
          </div>

          <div className="mt-6 flex flex-col items-center">
            <p className="text-[12px] text-white/80">Tự động làm mới sau</p>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-headline text-[34px] font-bold text-brand-orange leading-none">
                00:42
              </span>
            </div>
          </div>
        </section>

        <section className="mt-6 rounded-xl border border-white/20 bg-white/10 p-3 backdrop-blur">
          <p className="flex items-start gap-2 text-[13px] text-white/90">
            <Info className="mt-0.5 h-4 w-4 shrink-0" />
            Đưa mã QR cho nhân viên quét để tích điểm hoặc đổi quà
          </p>
        </section>

        <div className="mt-4 space-y-2.5">
          <button
            type="button"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-white py-3.5 font-headline font-bold text-brand-indigo shadow-lg active:scale-[0.98]"
          >
            <RefreshCw className="h-5 w-5" />
            Làm mới mã
          </button>
          <button
            type="button"
            className="w-full rounded-xl border border-white/40 py-3.5 text-[14px] font-medium text-white transition-colors hover:bg-white/10"
          >
            Hiển thị mã dự phòng
          </button>
        </div>
      </div>
    </div>
  );
}
