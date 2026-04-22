"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Info,
  Loader2,
  RefreshCw,
  Sun,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";

import { api } from "@/lib/api";
import { useMe } from "@/lib/hooks/use-me";

interface QrTokenResponse {
  jwt: string;
  exp_at_server: number;
  fallback_code: string;
}

export default function MemberQrPage() {
  const { data: user } = useMe();
  const { data, isLoading, isError, refetch } = useQuery<QrTokenResponse>({
    queryKey: ["member", "qr"],
    queryFn: async () => (await api.get<QrTokenResponse>("/member/qr")).data,
    refetchInterval: 55_000, // refresh mỗi 55s (TTL 120s)
  });

  const [remaining, setRemaining] = useState<number>(0);

  useEffect(() => {
    if (!data) return;
    const tick = () => {
      const diff = Math.max(
        0,
        data.exp_at_server * 1000 - Date.now()
      );
      setRemaining(Math.floor(diff / 1000));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [data]);

  const mm = Math.floor(remaining / 60)
    .toString()
    .padStart(2, "0");
  const ss = (remaining % 60).toString().padStart(2, "0");

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
            className="flex h-10 w-10 items-center justify-center rounded-full text-white hover:bg-white/10"
            aria-label="Độ sáng"
          >
            <Sun className="h-6 w-6" />
          </button>
        </header>

        <section className="rounded-2xl border border-white/20 bg-white/10 p-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-white/40 bg-gradient-to-br from-indigo-200 to-violet-200 text-[14px] font-bold text-indigo-700">
              {user?.full_name
                ?.split(/\s+/)
                .slice(-2)
                .map((p) => p[0]?.toUpperCase())
                .join("") ?? "M"}
            </div>
            <div className="flex-1">
              <p className="font-headline text-[15px] font-bold text-white">
                {user?.full_name ?? "Thành viên"}
              </p>
              <p className="text-[11px] text-white/70">
                {user?.phone ?? user?.email ?? "—"}
              </p>
            </div>
          </div>
        </section>

        <section className="mt-8 flex flex-1 flex-col items-center justify-center">
          <div className="rounded-3xl bg-white p-6 shadow-2xl">
            {isLoading ? (
              <div className="flex h-64 w-64 items-center justify-center">
                <Loader2 className="h-10 w-10 animate-spin text-brand-indigo" />
              </div>
            ) : isError || !data ? (
              <div className="flex h-64 w-64 flex-col items-center justify-center gap-3 text-center">
                <p className="text-[13px] text-red-600">
                  Không tạo được QR. Vui lòng thử lại.
                </p>
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="rounded-lg bg-brand-indigo px-4 py-2 text-[12px] font-bold text-white"
                >
                  Thử lại
                </button>
              </div>
            ) : (
              <div className="relative h-64 w-64">
                <QRCodeSVG
                  value={data.jwt}
                  size={256}
                  level="M"
                  marginSize={0}
                  bgColor="#ffffff"
                  fgColor="#0f172a"
                  imageSettings={{
                    src:
                      "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'><rect width='40' height='40' rx='20' fill='%234f46e5'/><text x='50%25' y='50%25' text-anchor='middle' dominant-baseline='central' font-family='sans-serif' font-size='22' font-weight='700' fill='white'>L</text></svg>",
                    height: 44,
                    width: 44,
                    excavate: true,
                  }}
                />
              </div>
            )}
            {data && (
              <p className="mt-3 text-center font-mono text-[11px] text-slate-400">
                Mã dự phòng: {data.fallback_code}
              </p>
            )}
          </div>

          <div className="mt-6 flex flex-col items-center">
            <p className="text-[12px] text-white/80">Tự động làm mới sau</p>
            <span className="mt-1 font-headline text-[34px] font-bold text-brand-orange">
              {mm}:{ss}
            </span>
          </div>
        </section>

        <section className="mt-4 rounded-xl border border-white/20 bg-white/10 p-3 backdrop-blur">
          <p className="flex items-start gap-2 text-[13px] text-white/90">
            <Info className="mt-0.5 h-4 w-4 shrink-0" />
            Đưa mã QR cho nhân viên quét để tích điểm hoặc đổi quà
          </p>
        </section>

        <div className="mt-4 space-y-2.5">
          <button
            type="button"
            onClick={() => refetch()}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-white py-3.5 font-headline font-bold text-brand-indigo shadow-lg active:scale-[0.98]"
          >
            <RefreshCw className="h-5 w-5" />
            Làm mới mã
          </button>
        </div>
      </div>
    </div>
  );
}

