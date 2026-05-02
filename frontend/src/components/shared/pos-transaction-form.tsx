"use client";

import {
  Camera,
  Check,
  CheckCircle2,
  Crown,
  Delete,
  Loader2,
  Phone,
  QrCode,
  Receipt,
  RefreshCcw,
  Sparkles,
  User,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import {
  useCreateQrTransaction,
  useCreateTransaction,
  useLookupCustomerByPhone,
  useLookupCustomerByQr,
} from "@/lib/hooks/use-partner";
import type {
  CustomerLookupResponse,
  TransactionWithMemberResponse,
} from "@/types/partner";

type PadKey =
  | "0" | "1" | "2" | "3" | "4"
  | "5" | "6" | "7" | "8" | "9"
  | "000" | "del";

const numberPad: readonly PadKey[] = [
  "1", "2", "3",
  "4", "5", "6",
  "7", "8", "9",
  "000", "0", "del",
];

function formatVnd(n: string | number): string {
  const num = typeof n === "string" ? Number(n) : n;
  if (!num || Number.isNaN(num)) return "0 ₫";
  return num.toLocaleString("vi-VN") + " ₫";
}

interface PosTransactionFormProps {
  /** Tone gradient header — indigo cho merchant, emerald cho staff */
  accentColor?: "indigo" | "emerald";
}

export function PosTransactionForm({
  accentColor = "indigo",
}: PosTransactionFormProps) {
  const [mode, setMode] = useState<"phone" | "qr">("phone");
  const [phone, setPhone] = useState("");
  const [qrPayload, setQrPayload] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [amount, setAmount] = useState("");
  const [receiptCode, setReceiptCode] = useState("");
  const [result, setResult] = useState<TransactionWithMemberResponse | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const createTxn = useCreateTransaction();
  const createQrTxn = useCreateQrTransaction();
  const submitting = createTxn.isPending || createQrTxn.isPending;

  // Lookup khách — auto-fire khi đủ điều kiện
  const phoneDigits = phone.replace(/\D/g, "");
  const phoneLookupReady = mode === "phone" && phoneDigits.length >= 10;
  const phoneLookup = useLookupCustomerByPhone(phone.trim(), phoneLookupReady);

  const qrLookupReady = mode === "qr" && qrPayload.trim().length > 0;
  const qrLookup = useLookupCustomerByQr(qrPayload.trim(), qrLookupReady);

  const phoneLocked = phoneLookupReady && phoneLookup.data?.found === true;

  const activeLookup = mode === "phone" ? phoneLookup.data : qrLookup.data;
  const memberDisabled =
    activeLookup?.is_member === true && activeLookup?.is_active === false;

  // BarcodeDetector — chrome/edge/android. Feature detect an toàn cho SSR.
  const hasBarcodeDetector =
    typeof window !== "undefined" && "BarcodeDetector" in window;

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
              setQrPayload(codes[0].rawValue);
              setScanning(false);
              return;
            }
          } catch {
            // Frame lỗi thì bỏ qua, giữ loop
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

  const handlePad = (key: PadKey) => {
    if (key === "del") {
      setAmount((v) => v.slice(0, -1));
      return;
    }
    if (key === "000") {
      setAmount((v) => (v === "" || v === "0" ? "" : v + "000"));
      return;
    }
    setAmount((v) => (v === "" || v === "0" ? key : v + key));
  };

  const handleSubmit = async () => {
    setError(null);
    setResult(null);
    if (!amount.trim() || Number(amount) <= 0) {
      setError("Vui lòng nhập số tiền hợp lệ");
      return;
    }
    if (memberDisabled) {
      setError(
        "Thành viên đã bị khoá tại đối tác — không thể tích điểm. Vui lòng mở khoá ở mục Thành viên trước."
      );
      return;
    }
    try {
      if (mode === "qr") {
        if (!qrPayload.trim()) {
          setError("Vui lòng quét QR khách trước khi tích điểm");
          return;
        }
        if (qrLookup.isError || qrLookup.data?.found !== true) {
          setError("QR không hợp lệ hoặc không tìm thấy khách hàng");
          return;
        }
        const res = await createQrTxn.mutateAsync({
          qr_payload: qrPayload.trim(),
          gross_amount: Number(amount),
          note: null,
          receipt_code: receiptCode.trim() || null,
        });
        setResult(res.data);
        setAmount("");
        setQrPayload("");
        setReceiptCode("");
        return;
      }
      if (!phone.trim()) {
        setError("Vui lòng nhập số điện thoại khách");
        return;
      }
      const res = await createTxn.mutateAsync({
        phone: phone.trim(),
        gross_amount: Number(amount),
        note: null,
        receipt_code: receiptCode.trim() || null,
      });
      setResult(res.data);
      setAmount("");
      setReceiptCode("");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? "Lỗi tạo giao dịch");
    }
  };

  const handleResetCustomer = () => {
    setPhone("");
    setQrPayload("");
    setScanning(false);
    setScanError(null);
    setError(null);
  };

  const handleReset = () => {
    handleResetCustomer();
    setAmount("");
    setReceiptCode("");
    setResult(null);
  };

  const handleRescan = () => {
    setQrPayload("");
    setScanError(null);
    setError(null);
    if (hasBarcodeDetector) {
      setScanning(true);
    }
  };

  const accentBg = accentColor === "emerald" ? "bg-emerald-700" : "bg-brand-indigo";
  const accentGradient =
    accentColor === "emerald"
      ? "from-emerald-700 to-emerald-900 shadow-emerald-200"
      : "from-brand-indigo to-brand-violet shadow-indigo-200";
  const accentLight =
    accentColor === "emerald" ? "bg-emerald-50 text-emerald-700" : "bg-indigo-50 text-brand-indigo";

  const qrErrorDetail = (qrLookup.error as { response?: { data?: { detail?: string } } } | null)?.response?.data?.detail;

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-5">
      {/* Form */}
      <section className="space-y-5 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-3">
        {/* Khách hàng */}
        <div>
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Khách hàng
          </h2>
          <div className="mt-3 flex w-fit items-center gap-1 rounded-full bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => {
                setMode("phone");
                setQrPayload("");
                setScanning(false);
                setScanError(null);
              }}
              className={
                mode === "phone"
                  ? `flex items-center gap-1.5 rounded-full ${accentBg} px-4 py-2 text-[12px] font-bold text-white shadow`
                  : "flex items-center gap-1.5 rounded-full px-4 py-2 text-[12px] font-medium text-slate-500"
              }
            >
              <Phone className="h-3.5 w-3.5" />
              Số điện thoại
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("qr");
                setPhone("");
              }}
              className={
                mode === "qr"
                  ? `flex items-center gap-1.5 rounded-full ${accentBg} px-4 py-2 text-[12px] font-bold text-white shadow`
                  : "flex items-center gap-1.5 rounded-full px-4 py-2 text-[12px] font-medium text-slate-500"
              }
            >
              <QrCode className="h-3.5 w-3.5" />
              Quét QR
            </button>
          </div>

          {mode === "phone" ? (
            <div className="mt-3 space-y-3">
              <div className="relative">
                <Phone className="pointer-events-none absolute inset-y-0 left-4 my-auto h-5 w-5 text-slate-400" />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={phoneLocked}
                  placeholder="Nhập số điện thoại khách hàng (vd: 0901234501)"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-4 pl-12 pr-3 text-[16px] font-medium outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20 disabled:bg-slate-100 disabled:text-slate-500"
                />
              </div>

              {phoneLookupReady && phoneLookup.isFetching && (
                <p className="flex items-center gap-1.5 text-[12px] text-slate-500">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Đang tra cứu khách hàng...
                </p>
              )}

              {phoneLookup.data && phoneLookup.data.found && (
                <CustomerInfoCard
                  data={phoneLookup.data}
                  onChange={handleResetCustomer}
                />
              )}

              {phoneLookupReady &&
                !phoneLookup.isFetching &&
                phoneLookup.data?.found === false && (
                  <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[12px] text-amber-800">
                    <p className="flex items-center gap-1.5 font-medium">
                      <Sparkles className="h-3.5 w-3.5" />
                      Khách chưa có tài khoản
                    </p>
                    <p className="mt-0.5 text-amber-700">
                      Hệ thống sẽ tự tạo tài khoản mới khi tích điểm.
                    </p>
                  </div>
                )}
            </div>
          ) : (
            <div className="mt-3 space-y-3">
              {qrPayload.trim() === "" ? (
                <>
                  {scanning ? (
                    <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-black">
                      <video
                        ref={videoRef}
                        className="h-56 w-full object-cover"
                        playsInline
                        muted
                      />
                      <button
                        type="button"
                        onClick={() => setScanning(false)}
                        className="absolute right-2 top-2 rounded-lg bg-white/90 px-3 py-1 text-[11px] font-bold text-slate-700"
                      >
                        Dừng
                      </button>
                      <div className="pointer-events-none absolute inset-6 rounded-xl border-2 border-white/70" />
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setScanError(null);
                        if (!hasBarcodeDetector) {
                          setScanError(
                            "Trình duyệt không hỗ trợ quét camera — vui lòng dùng trình duyệt Chrome/Edge trên Android hoặc desktop"
                          );
                          return;
                        }
                        setScanning(true);
                      }}
                      className={`flex w-full items-center justify-center gap-2 rounded-xl ${accentBg} py-4 text-[14px] font-bold text-white`}
                    >
                      <Camera className="h-5 w-5" />
                      Quét bằng camera
                    </button>
                  )}
                  {scanError && (
                    <p className="text-[12px] text-amber-700">{scanError}</p>
                  )}
                </>
              ) : qrLookup.isFetching ? (
                <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
                  <p className="flex items-center gap-1.5 text-[13px] text-slate-600">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Đang xác thực QR...
                  </p>
                </div>
              ) : qrLookup.data?.found ? (
                <>
                  <CustomerInfoCard
                    data={qrLookup.data}
                    onChange={handleRescan}
                    changeLabel="Quét QR khác"
                  />
                </>
              ) : (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                  <p className="flex items-center gap-1.5 text-[13px] font-bold text-red-700">
                    <RefreshCcw className="h-4 w-4" />
                    QR không hợp lệ
                  </p>
                  <p className="mt-1 text-[12px] text-red-600">
                    {qrErrorDetail ?? "Không thể xác thực QR này. Vui lòng thử quét QR khác."}
                  </p>
                  <button
                    type="button"
                    onClick={handleRescan}
                    className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 py-2 text-[13px] font-bold text-white hover:bg-red-700"
                  >
                    <Camera className="h-4 w-4" />
                    Quét QR khác
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Số tiền */}
        <div className="border-t border-slate-100 pt-4">
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Số tiền giao dịch
          </h2>
          <div className="mt-3 flex h-20 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 px-6">
            <span className="font-headline text-[32px] font-bold text-brand-orange">
              {formatVnd(amount)}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2">
            {numberPad.map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => handlePad(key)}
                className={`flex h-14 items-center justify-center rounded-xl ${accentLight} text-[22px] font-bold transition-transform hover:opacity-80 active:scale-95`}
              >
                {key === "del" ? <Delete className="h-5 w-5" /> : key}
              </button>
            ))}
          </div>
        </div>

        {/* Mã hoá đơn — áp dụng cho cả luồng phone và QR */}
        <div className="border-t border-slate-100 pt-4">
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Mã hoá đơn{" "}
            <span className="text-[11px] font-normal text-slate-400">
              (tuỳ chọn)
            </span>
          </h2>
          <p className="mt-1 text-[11px] text-slate-500">
            Tham chiếu tới hoá đơn/bill trên hệ thống POS của shop
          </p>
          <div className="relative mt-3">
            <Receipt className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={receiptCode}
              onChange={(e) => setReceiptCode(e.target.value)}
              maxLength={50}
              placeholder="VD: HD-00123"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
            />
          </div>
        </div>
      </section>

      {/* Summary */}
      <aside className="h-fit space-y-5 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-2">
        <section>
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Chi tiết giao dịch
          </h2>
          <ul className="mt-3 space-y-2 text-[13px]">
            <li className="flex items-center justify-between">
              <span className="text-slate-500">Tổng tiền</span>
              <span className="font-medium text-slate-800">
                {formatVnd(amount)}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-slate-500">Khách</span>
              <span className="font-medium text-slate-800">
                {(() => {
                  const lookup =
                    mode === "phone" ? phoneLookup.data : qrLookup.data;
                  if (lookup?.found) {
                    return lookup.full_name ?? lookup.phone ?? `User #${lookup.user_id}`;
                  }
                  if (mode === "phone") return phone || "—";
                  return qrPayload ? `QR (${qrPayload.slice(0, 20)}...)` : "—";
                })()}
              </span>
            </li>
          </ul>
        </section>

        {error && (
          <div className="rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-600">
            {error}
          </div>
        )}

        {result && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-center gap-2">
              <Check className="h-5 w-5 text-emerald-600" />
              <span className="font-bold text-emerald-800">
                Tích điểm thành công!
              </span>
            </div>
            <div className="mt-3 space-y-1 text-[13px] text-emerald-900">
              <p>
                <span className="text-slate-600">Khách:</span>{" "}
                {result.member_full_name ?? result.member_phone}
              </p>
              <p>
                <span className="text-slate-600">Điểm mới:</span>{" "}
                <span className="font-bold text-brand-orange">
                  +{result.transaction.points_earned}
                </span>
              </p>
              <p>
                <span className="text-slate-600">Tổng điểm:</span>{" "}
                <span className="font-bold">{result.new_balance}</span>
              </p>
              {result.tier_upgraded && (
                <p className="mt-2 flex items-center gap-1 rounded-lg bg-amber-100 px-2 py-1 font-bold text-amber-800">
                  <Crown className="h-4 w-4" fill="currentColor" />
                  Đã lên hạng {result.new_tier_name}
                </p>
              )}
            </div>
          </div>
        )}

        <div className="space-y-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || memberDisabled}
            className={`flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r ${accentGradient} py-3 font-headline text-[14px] font-bold text-white shadow-lg active:scale-[0.98] disabled:opacity-60`}
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            {submitting ? "Đang tích..." : "Xác nhận tích điểm"}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="w-full rounded-xl border border-slate-200 py-3 text-[13px] font-medium text-slate-600 hover:bg-slate-50"
          >
            Huỷ / Làm mới
          </button>
        </div>
      </aside>
    </div>
  );
}

function CustomerInfoCard({
  data,
  onChange,
  changeLabel = "Đổi khách",
}: {
  data: CustomerLookupResponse;
  onChange: () => void;
  changeLabel?: string;
}) {
  const disabled = data.is_member && data.is_active === false;
  const containerCls = disabled
    ? "rounded-xl border border-red-200 bg-red-50 px-4 py-3"
    : "rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3";
  const avatarCls = disabled
    ? "flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-200 text-red-800"
    : "flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-200 text-emerald-800";
  const nameCls = disabled
    ? "flex items-center gap-1.5 text-[13px] font-bold text-red-900"
    : "flex items-center gap-1.5 text-[13px] font-bold text-emerald-900";
  const phoneCls = disabled ? "text-[12px] text-red-800" : "text-[12px] text-emerald-800";
  const buttonCls = disabled
    ? "shrink-0 rounded-lg border border-red-300 bg-white px-2 py-1 text-[11px] font-medium text-red-700 hover:bg-red-100"
    : "shrink-0 rounded-lg border border-emerald-300 bg-white px-2 py-1 text-[11px] font-medium text-emerald-700 hover:bg-emerald-100";

  return (
    <div className={containerCls}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className={avatarCls}>
            <User className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className={nameCls}>
              <CheckCircle2 className="h-3.5 w-3.5" />
              {data.full_name || "Khách hàng"}
              {disabled && (
                <span className="ml-1 rounded-full bg-red-200 px-2 py-0.5 text-[10px] font-bold uppercase text-red-800">
                  Đã khoá
                </span>
              )}
            </p>
            <p className={phoneCls}>
              {data.phone ?? "—"}
            </p>
            {disabled ? (
              <p className="mt-1 text-[11px] font-medium text-red-700">
                Thành viên đã bị khoá tại shop — không thể tích điểm. Vui lòng mở khoá ở mục Thành viên trước.
              </p>
            ) : data.is_member ? (
              <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
                <span className="rounded-full bg-white/70 px-2 py-0.5 font-medium text-emerald-900">
                  Điểm: {(data.points_balance ?? 0).toLocaleString("vi-VN")}
                </span>
                {data.current_tier_name && (
                  <span className="flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 font-bold text-amber-800">
                    <Crown className="h-3 w-3" fill="currentColor" />
                    {data.current_tier_name}
                  </span>
                )}
              </div>
            ) : (
              <div className="mt-2 rounded-md bg-amber-50 border border-amber-300 px-2 py-1.5">
                <p className="text-[11px] font-medium text-amber-800">Khách mới — chưa là thành viên shop</p>
                <p className="text-[10px] text-amber-700">
                  Sau khi xác nhận tích điểm, hệ thống sẽ tự đăng ký thành viên cho khách này.
                </p>
              </div>
            )}
          </div>
        </div>
        <button type="button" onClick={onChange} className={buttonCls}>
          {changeLabel}
        </button>
      </div>
    </div>
  );
}
