"use client";

import {
  Camera,
  CheckCircle2,
  Keyboard,
  Loader2,
  QrCode,
  RefreshCcw,
  Ticket,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";

import { redemptionsApi } from "@/lib/api-partner";
import type { RedemptionUseResponse } from "@/lib/api-partner";

const CODE_LENGTH = 8;

function normalizeCode(raw: string): string {
  return raw.replace(/\s+/g, "").toUpperCase().slice(0, CODE_LENGTH);
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StaffUseRedemptionPage() {
  const [mode, setMode] = useState<"manual" | "qr">("manual");
  const [code, setCode] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const hasBarcodeDetector =
    typeof window !== "undefined" && "BarcodeDetector" in window;

  const useRedemption = useMutation<RedemptionUseResponse, unknown, string>({
    mutationFn: async (c: string) => {
      const res = await redemptionsApi.use(c);
      return res.data;
    },
  });

  useEffect(() => {
    if (!scanning) return;
    let stream: MediaStream | null = null;
    let rafId: number | null = null;
    let cancelled = false;

    const start = async () => {
      try {
        // @ts-expect-error BarcodeDetector chưa có trong TS lib.dom mặc định
        const detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        const video = videoRef.current;
        if (!video) return;
        video.srcObject = stream;
        await video.play();

        const tick = async () => {
          if (cancelled || !videoRef.current) return;
          try {
            const codes = await detector.detect(videoRef.current);
            if (codes.length > 0 && codes[0].rawValue) {
              const c = normalizeCode(codes[0].rawValue);
              if (c.length === CODE_LENGTH) {
                setCode(c);
                setScanning(false);
                useRedemption.mutate(c);
                return;
              }
            }
          } catch {
            // skip frame
          }
          rafId = requestAnimationFrame(tick);
        };
        rafId = requestAnimationFrame(tick);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setScanError("Không mở được camera: " + msg);
        setScanning(false);
      }
    };
    start();

    return () => {
      cancelled = true;
      if (rafId != null) cancelAnimationFrame(rafId);
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, [scanning]);

  const handleSubmit = () => {
    if (code.length !== CODE_LENGTH) return;
    useRedemption.mutate(code);
  };

  const handleReset = () => {
    setCode("");
    setScanError(null);
    useRedemption.reset();
  };

  const errorMessage = (() => {
    if (!useRedemption.isError) return null;
    const err = useRedemption.error;
    if (axios.isAxiosError(err)) {
      const detail = (err.response?.data as { detail?: string } | undefined)
        ?.detail;
      if (detail) return detail;
      if (err.response?.status === 404)
        return "Mã không tồn tại hoặc không thuộc cửa hàng này.";
    }
    return "Không xác nhận được mã. Thử lại.";
  })();

  const result = useRedemption.data;
  const success = result?.status === "used";

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Cửa hàng / Dùng voucher</p>
        <h1 className="mt-1 font-headline text-[28px] font-bold text-slate-800 md:text-[32px]">
          Quét voucher / quà tặng
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Quét QR voucher hoặc nhập mã 8 ký tự để xác nhận khách đã dùng.
        </p>
      </header>

      {/* Result card */}
      {result && (
        <section
          className={`mt-6 rounded-2xl border p-5 shadow-sm ${
            success
              ? "border-emerald-200 bg-emerald-50"
              : "border-amber-200 bg-amber-50"
          }`}
        >
          <div className="flex items-start gap-3">
            <CheckCircle2
              className={`h-6 w-6 shrink-0 ${
                success ? "text-emerald-600" : "text-amber-600"
              }`}
            />
            <div className="flex-1 space-y-2">
              <p
                className={`font-headline text-[18px] font-bold ${
                  success ? "text-emerald-700" : "text-amber-700"
                }`}
              >
                {success
                  ? "Đã xác nhận sử dụng"
                  : `Trạng thái: ${result.status}`}
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[13px] text-slate-700">
                <span className="text-slate-500">Mã</span>
                <span className="font-mono font-bold tracking-wider">
                  {result.redemption_code}
                </span>
                <span className="text-slate-500">Điểm đã dùng</span>
                <span className="font-bold">
                  {result.points_spent.toLocaleString("vi-VN")} điểm
                </span>
                <span className="text-slate-500">Đổi lúc</span>
                <span>{formatDateTime(result.redeemed_at)}</span>
                <span className="text-slate-500">Dùng lúc</span>
                <span>{formatDateTime(result.used_at)}</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={handleReset}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50"
          >
            <RefreshCcw className="h-4 w-4" />
            Quét mã khác
          </button>
        </section>
      )}

      {/* Error */}
      {errorMessage && !result && (
        <section className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4">
          <p className="text-[14px] font-medium text-red-700">{errorMessage}</p>
          <button
            type="button"
            onClick={handleReset}
            className="mt-3 text-[13px] font-bold text-red-700 underline"
          >
            Thử lại
          </button>
        </section>
      )}

      {/* Input area — ẩn sau khi đã xác nhận thành công */}
      {!result && (
        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex gap-2">
            <button
              type="button"
              onClick={() => {
                setMode("manual");
                setScanning(false);
              }}
              className={`flex-1 rounded-lg px-3 py-2 text-[13px] font-bold transition-colors ${
                mode === "manual"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              <Keyboard className="mr-1.5 inline h-4 w-4" />
              Nhập mã
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("qr");
                setScanError(null);
              }}
              className={`flex-1 rounded-lg px-3 py-2 text-[13px] font-bold transition-colors ${
                mode === "qr"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              <QrCode className="mr-1.5 inline h-4 w-4" />
              Quét QR
            </button>
          </div>

          {mode === "manual" && (
            <div className="space-y-3">
              <label
                htmlFor="redeem-code"
                className="block text-[13px] font-medium text-slate-600"
              >
                Mã đổi quà (8 ký tự)
              </label>
              <input
                id="redeem-code"
                type="text"
                value={code}
                onChange={(e) => setCode(normalizeCode(e.target.value))}
                placeholder="VD: CK3D8SCA"
                autoComplete="off"
                spellCheck={false}
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 font-mono text-[18px] font-bold uppercase tracking-[0.25em] text-slate-800 focus:border-emerald-500 focus:outline-none"
              />
              <button
                type="button"
                disabled={
                  code.length !== CODE_LENGTH || useRedemption.isPending
                }
                onClick={handleSubmit}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-3 text-[14px] font-bold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:bg-slate-300"
              >
                {useRedemption.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Đang xác nhận...
                  </>
                ) : (
                  <>
                    <Ticket className="h-4 w-4" />
                    Xác nhận dùng
                  </>
                )}
              </button>
            </div>
          )}

          {mode === "qr" && (
            <div className="space-y-3">
              {!hasBarcodeDetector ? (
                <p className="rounded-lg bg-amber-50 p-3 text-[13px] text-amber-700">
                  Trình duyệt này không hỗ trợ quét QR. Hãy dùng Chrome/Edge
                  trên Android, hoặc nhập mã thủ công.
                </p>
              ) : !scanning ? (
                <button
                  type="button"
                  onClick={() => {
                    setScanError(null);
                    setScanning(true);
                  }}
                  className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-emerald-300 bg-emerald-50 py-10 text-[14px] font-bold text-emerald-700 hover:bg-emerald-100"
                >
                  <Camera className="h-5 w-5" />
                  Mở camera quét QR
                </button>
              ) : (
                <div className="relative overflow-hidden rounded-lg bg-black">
                  <video
                    ref={videoRef}
                    className="aspect-square w-full object-cover"
                    playsInline
                    muted
                  />
                  <button
                    type="button"
                    onClick={() => setScanning(false)}
                    className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white"
                    aria-label="Đóng"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <p className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-black/60 px-3 py-1 text-[11px] text-white">
                    Đưa QR voucher vào khung
                  </p>
                </div>
              )}
              {scanError && (
                <p className="rounded-lg bg-red-50 p-3 text-[13px] text-red-700">
                  {scanError}
                </p>
              )}
              {useRedemption.isPending && (
                <p className="flex items-center gap-2 text-[13px] text-slate-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Đang xác nhận mã...
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
