"use client";

import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Gift,
  Loader2,
  Phone,
  QrCode,
  RefreshCcw,
  Search,
  Ticket,
  User as UserIcon,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";

import {
  redemptionsApi,
  transactionsApi,
  type RedemptionInspectResponse,
  type RedemptionUseResponse,
} from "@/lib/api-partner";
import type { CustomerLookupResponse } from "@/types/partner";

const CODE_LENGTH = 8;

function normalizeCode(raw: string): string {
  return raw.replace(/\s+/g, "").toUpperCase().slice(0, CODE_LENGTH);
}

function formatVnd(n: number): string {
  return n.toLocaleString("vi-VN") + "đ";
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function extractDetail(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: string } | undefined)
      ?.detail;
    if (detail) return detail;
  }
  return fallback;
}

type ScanTarget = "voucher" | "customer" | null;

export default function StaffUseRedemptionPage() {
  const [voucherCodeInput, setVoucherCodeInput] = useState("");
  const [voucher, setVoucher] = useState<RedemptionInspectResponse | null>(null);
  const [voucherErr, setVoucherErr] = useState<string | null>(null);

  const [phoneInput, setPhoneInput] = useState("");
  const [customer, setCustomer] = useState<CustomerLookupResponse | null>(null);
  const [customerErr, setCustomerErr] = useState<string | null>(null);

  const [billAmount, setBillAmount] = useState<string>("");

  const [scanTarget, setScanTarget] = useState<ScanTarget>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [success, setSuccess] = useState<RedemptionUseResponse | null>(null);

  const hasBarcodeDetector =
    typeof window !== "undefined" && "BarcodeDetector" in window;

  const inspectMut = useMutation({
    mutationFn: async (code: string) => {
      const res = await redemptionsApi.inspect(code);
      return res.data;
    },
    onSuccess: (data) => {
      setVoucher(data);
      setVoucherErr(null);
    },
    onError: (err) => {
      setVoucher(null);
      setVoucherErr(extractDetail(err, "Không tra cứu được mã."));
    },
  });

  const lookupPhoneMut = useMutation({
    mutationFn: async (phone: string) => {
      const res = await transactionsApi.lookupByPhone(phone);
      return res.data;
    },
    onSuccess: (data) => {
      if (!data.found || !data.user_id) {
        setCustomer(null);
        setCustomerErr("Khách chưa có tài khoản. Hãy mời khách đăng ký.");
        return;
      }
      setCustomer(data);
      setCustomerErr(null);
    },
    onError: (err) => {
      setCustomer(null);
      setCustomerErr(extractDetail(err, "Không tra cứu được số điện thoại."));
    },
  });

  const lookupQrMut = useMutation({
    mutationFn: async (qr: string) => {
      const res = await transactionsApi.lookupByQr(qr);
      return res.data;
    },
    onSuccess: (data) => {
      if (!data.found || !data.user_id) {
        setCustomer(null);
        setCustomerErr("QR cá nhân không hợp lệ.");
        return;
      }
      setCustomer(data);
      setCustomerErr(null);
    },
    onError: (err) => {
      setCustomer(null);
      setCustomerErr(extractDetail(err, "QR cá nhân không hợp lệ."));
    },
  });

  const useMut = useMutation({
    mutationFn: async (vars: {
      code: string;
      originalAmount: number | null;
      expectedUserId: number | null;
    }) => {
      const res = await redemptionsApi.use(
        vars.code,
        vars.originalAmount,
        vars.expectedUserId
      );
      return res.data;
    },
    onSuccess: (data) => setSuccess(data),
  });

  // Camera scan
  useEffect(() => {
    if (!scanTarget) return;
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
              const raw = codes[0].rawValue as string;
              if (scanTarget === "voucher") {
                const c = normalizeCode(raw);
                if (c.length === CODE_LENGTH) {
                  setVoucherCodeInput(c);
                  setScanTarget(null);
                  inspectMut.mutate(c);
                  return;
                }
              } else if (scanTarget === "customer") {
                setScanTarget(null);
                lookupQrMut.mutate(raw);
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
        setScanTarget(null);
      }
    };
    start();

    return () => {
      cancelled = true;
      if (rafId != null) cancelAnimationFrame(rafId);
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanTarget]);

  const handleVoucherLookup = () => {
    if (voucherCodeInput.length !== CODE_LENGTH) return;
    inspectMut.mutate(voucherCodeInput);
  };
  const handleResetVoucher = () => {
    setVoucher(null);
    setVoucherErr(null);
    setVoucherCodeInput("");
    inspectMut.reset();
  };

  const handlePhoneLookup = () => {
    const p = phoneInput.trim();
    if (!p) return;
    lookupPhoneMut.mutate(p);
  };
  const handleResetCustomer = () => {
    setCustomer(null);
    setCustomerErr(null);
    setPhoneInput("");
    lookupPhoneMut.reset();
    lookupQrMut.reset();
  };

  const handleResetAll = () => {
    handleResetVoucher();
    handleResetCustomer();
    setBillAmount("");
    setSuccess(null);
    useMut.reset();
  };

  const offerType = voucher?.reward.offer_type;
  const isItemGift = offerType === "ITEM_GIFT";
  const isDiscount =
    offerType === "PERCENT_DISCOUNT" || offerType === "FIXED_DISCOUNT";

  const billNumber = (() => {
    const n = parseInt(billAmount.replace(/[^0-9]/g, ""), 10);
    return Number.isFinite(n) && n > 0 ? n : 0;
  })();

  const computedDiscount = (() => {
    if (!voucher || !isDiscount || billNumber <= 0) return 0;
    const v = voucher.reward.offer_value ?? 0;
    if (offerType === "PERCENT_DISCOUNT") {
      return Math.min(billNumber, Math.floor((billNumber * v) / 100));
    }
    return Math.min(billNumber, v);
  })();
  const finalAmount = Math.max(0, billNumber - computedDiscount);

  const userMatch =
    voucher && customer && voucher.customer.user_id === customer.user_id;
  const userMismatch =
    voucher && customer && voucher.customer.user_id !== customer.user_id;

  const canConfirm =
    !!voucher &&
    !!customer &&
    !!userMatch &&
    !useMut.isPending &&
    (isItemGift || (isDiscount && billNumber > 0));

  const handleConfirm = () => {
    if (!voucher || !customer || !canConfirm) return;
    useMut.mutate({
      code: voucher.redemption_code,
      originalAmount: isDiscount ? billNumber : null,
      expectedUserId: customer.user_id,
    });
  };

  // ───────────── Success view ─────────────
  if (success) {
    return (
      <main className="px-4 py-5 md:px-8 md:py-6">
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-6 w-6 shrink-0 text-emerald-600" />
            <div className="flex-1 space-y-2">
              <p className="font-headline text-[20px] font-bold text-emerald-700">
                Đã xác nhận sử dụng voucher
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[13px] text-slate-700">
                <span className="text-slate-500">Mã</span>
                <span className="font-mono font-bold tracking-wider">
                  {success.redemption_code}
                </span>
                <span className="text-slate-500">Điểm đã dùng</span>
                <span className="font-bold">
                  {success.points_spent.toLocaleString("vi-VN")} điểm
                </span>
                {success.original_amount != null && (
                  <>
                    <span className="text-slate-500">Tổng hoá đơn</span>
                    <span>{formatVnd(success.original_amount)}</span>
                    <span className="text-slate-500">Giảm</span>
                    <span className="font-bold text-emerald-700">
                      −{formatVnd(success.discount_amount ?? 0)}
                    </span>
                    <span className="text-slate-500">Khách trả</span>
                    <span className="font-bold">
                      {formatVnd(
                        success.original_amount - (success.discount_amount ?? 0)
                      )}
                    </span>
                  </>
                )}
                <span className="text-slate-500">Dùng lúc</span>
                <span>{success.used_at ? formatDateTime(success.used_at) : "—"}</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={handleResetAll}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50"
          >
            <RefreshCcw className="h-4 w-4" />
            Dùng voucher khác
          </button>
        </section>
      </main>
    );
  }

  // ───────────── Working view ─────────────
  return (
    <main className="px-4 py-5 md:px-8 md:py-6 space-y-5">
      <header>
        <p className="text-[12px] text-slate-400">Cửa hàng / Dùng voucher</p>
        <h1 className="mt-1 font-headline text-[28px] font-bold text-slate-800 md:text-[32px]">
          Dùng voucher
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Quét/nhập voucher và xác minh khách. Bấm Xác nhận sau khi đủ thông tin.
        </p>
      </header>

      {/* Camera modal */}
      {scanTarget && (
        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[13px] font-bold text-slate-700">
              {scanTarget === "voucher"
                ? "Quét QR voucher"
                : "Quét QR cá nhân khách"}
            </p>
            <button
              type="button"
              onClick={() => setScanTarget(null)}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100"
              aria-label="Đóng"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          {!hasBarcodeDetector ? (
            <p className="rounded-lg bg-amber-50 p-3 text-[13px] text-amber-700">
              Trình duyệt không hỗ trợ quét QR. Hãy nhập tay.
            </p>
          ) : (
            <div className="relative overflow-hidden rounded-lg bg-black">
              <video
                ref={videoRef}
                className="aspect-square w-full object-cover"
                playsInline
                muted
              />
              <p className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-black/60 px-3 py-1 text-[11px] text-white">
                Đưa QR vào khung
              </p>
            </div>
          )}
          {scanError && (
            <p className="mt-2 rounded-lg bg-red-50 p-3 text-[13px] text-red-700">
              {scanError}
            </p>
          )}
        </section>
      )}

      {/* Slot 1 — Voucher */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-[12px] font-bold text-white">
            1
          </span>
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Voucher
          </h2>
          <Ticket className="h-4 w-4 text-amber-500" />
        </div>

        {voucher ? (
          <VoucherCard voucher={voucher} onReset={handleResetVoucher} />
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={voucherCodeInput}
                onChange={(e) =>
                  setVoucherCodeInput(normalizeCode(e.target.value))
                }
                placeholder="Mã 8 ký tự, VD: CK3D8SCA"
                autoComplete="off"
                spellCheck={false}
                className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-mono text-[16px] font-bold uppercase tracking-[0.2em] focus:border-amber-500 focus:outline-none"
              />
              <button
                type="button"
                disabled={
                  voucherCodeInput.length !== CODE_LENGTH ||
                  inspectMut.isPending
                }
                onClick={handleVoucherLookup}
                className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-4 py-2.5 text-[13px] font-bold text-white hover:bg-amber-600 disabled:bg-slate-300"
              >
                {inspectMut.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Tra cứu
              </button>
            </div>
            <button
              type="button"
              onClick={() => {
                setScanError(null);
                setScanTarget("voucher");
              }}
              className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-amber-300 bg-amber-50 py-3 text-[13px] font-bold text-amber-700 hover:bg-amber-100"
            >
              <QrCode className="h-4 w-4" />
              Quét QR voucher
            </button>
            {voucherErr && (
              <p className="rounded-lg bg-red-50 p-3 text-[13px] text-red-700">
                {voucherErr}
              </p>
            )}
          </div>
        )}
      </section>

      {/* Slot 2 — Customer */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-[12px] font-bold text-white">
            2
          </span>
          <h2 className="font-headline text-[16px] font-bold text-slate-800">
            Khách hàng
          </h2>
          <UserIcon className="h-4 w-4 text-emerald-600" />
        </div>

        {customer ? (
          <CustomerCard customer={customer} onReset={handleResetCustomer} />
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Phone className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
                <input
                  type="tel"
                  value={phoneInput}
                  onChange={(e) => setPhoneInput(e.target.value)}
                  placeholder="Số điện thoại khách"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-[14px] focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <button
                type="button"
                disabled={!phoneInput.trim() || lookupPhoneMut.isPending}
                onClick={handlePhoneLookup}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2.5 text-[13px] font-bold text-white hover:bg-emerald-700 disabled:bg-slate-300"
              >
                {lookupPhoneMut.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Tìm
              </button>
            </div>
            <button
              type="button"
              onClick={() => {
                setScanError(null);
                setScanTarget("customer");
              }}
              className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-emerald-300 bg-emerald-50 py-3 text-[13px] font-bold text-emerald-700 hover:bg-emerald-100"
            >
              <Camera className="h-4 w-4" />
              Quét QR cá nhân
            </button>
            {customerErr && (
              <p className="rounded-lg bg-red-50 p-3 text-[13px] text-red-700">
                {customerErr}
              </p>
            )}
            {lookupQrMut.isPending && (
              <p className="flex items-center gap-2 text-[13px] text-slate-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang xác thực QR...
              </p>
            )}
          </div>
        )}
      </section>

      {/* Mismatch warning */}
      {userMismatch && (
        <section className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          <div className="text-[13px] text-red-700">
            <p className="font-bold">Voucher không thuộc khách này.</p>
            <p>
              Voucher của <b>{voucher?.customer.full_name ?? "khách khác"}</b>,
              khách đang xác minh là <b>{customer?.full_name ?? "—"}</b>. Hãy
              kiểm tra lại.
            </p>
          </div>
        </section>
      )}

      {/* Slot 3 — Bill amount + confirm */}
      {voucher && customer && userMatch && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-[12px] font-bold text-white">
              3
            </span>
            <h2 className="font-headline text-[16px] font-bold text-slate-800">
              Xác nhận
            </h2>
          </div>

          {isDiscount && (
            <div className="space-y-3">
              <label
                htmlFor="bill"
                className="block text-[13px] font-medium text-slate-600"
              >
                Tổng hoá đơn (VND)
              </label>
              <input
                id="bill"
                type="text"
                inputMode="numeric"
                value={billAmount}
                onChange={(e) =>
                  setBillAmount(e.target.value.replace(/[^0-9]/g, ""))
                }
                placeholder="VD: 250000"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-[16px] font-bold focus:border-indigo-500 focus:outline-none"
              />
              {billNumber > 0 && (
                <div className="rounded-lg bg-slate-50 p-3 text-[13px]">
                  <div className="grid grid-cols-2 gap-y-1">
                    <span className="text-slate-500">Tổng bill</span>
                    <span className="text-right font-medium">
                      {formatVnd(billNumber)}
                    </span>
                    <span className="text-slate-500">
                      Giảm ({voucher.reward.offer_label})
                    </span>
                    <span className="text-right font-bold text-emerald-700">
                      −{formatVnd(computedDiscount)}
                    </span>
                    <span className="border-t border-slate-200 pt-1 font-bold text-slate-700">
                      Khách trả
                    </span>
                    <span className="border-t border-slate-200 pt-1 text-right font-bold text-slate-800">
                      {formatVnd(finalAmount)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {isItemGift && (
            <div className="flex items-center gap-2 rounded-lg bg-amber-50 p-3 text-[13px] text-amber-700">
              <Gift className="h-4 w-4" />
              Voucher hiện vật — đưa quà cho khách rồi bấm Xác nhận.
            </div>
          )}

          {useMut.isError && (
            <p className="mt-3 rounded-lg bg-red-50 p-3 text-[13px] text-red-700">
              {extractDetail(useMut.error, "Xác nhận thất bại.")}
            </p>
          )}

          <button
            type="button"
            disabled={!canConfirm}
            onClick={handleConfirm}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-700 px-4 py-3 text-[15px] font-bold text-white shadow-sm transition-colors hover:brightness-105 disabled:opacity-60"
          >
            {useMut.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang xác nhận...
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4" />
                Xác nhận dùng voucher
              </>
            )}
          </button>
        </section>
      )}
    </main>
  );
}

function VoucherCard({
  voucher,
  onReset,
}: {
  voucher: RedemptionInspectResponse;
  onReset: () => void;
}) {
  const { reward, customer } = voucher;
  return (
    <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
      <div className="flex items-start gap-3">
        {reward.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={reward.image_url}
            alt={reward.name}
            className="h-16 w-16 shrink-0 rounded-lg object-cover"
          />
        ) : (
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-amber-200 text-amber-700">
            <Ticket className="h-7 w-7" />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <p className="font-headline text-[15px] font-bold text-slate-800">
            {reward.name}
          </p>
          <p className="text-[12px] font-medium text-amber-700">
            {reward.offer_label}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Mã{" "}
            <span className="font-mono font-bold tracking-wider">
              {voucher.redemption_code}
            </span>{" "}
            · {voucher.points_spent.toLocaleString("vi-VN")} điểm
          </p>
        </div>
      </div>
      <div className="rounded-md bg-white p-2 text-[12px]">
        <p className="text-slate-500">Chủ voucher</p>
        <p className="font-bold text-slate-800">
          {customer.full_name ?? "—"}{" "}
          {customer.phone && (
            <span className="font-normal text-slate-500">· {customer.phone}</span>
          )}
        </p>
      </div>
      <button
        type="button"
        onClick={onReset}
        className="text-[12px] font-bold text-amber-700 underline"
      >
        Dùng voucher khác
      </button>
    </div>
  );
}

function CustomerCard({
  customer,
  onReset,
}: {
  customer: CustomerLookupResponse;
  onReset: () => void;
}) {
  return (
    <div className="space-y-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3">
      <div className="flex items-start gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-emerald-200 text-emerald-700">
          <UserIcon className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-headline text-[15px] font-bold text-slate-800">
            {customer.full_name ?? "—"}
          </p>
          <p className="text-[12px] text-slate-600">
            {customer.phone ?? "—"}{" "}
            {customer.email && (
              <span className="text-slate-400">· {customer.email}</span>
            )}
          </p>
          {customer.points_balance != null && (
            <p className="mt-0.5 text-[11px] text-slate-500">
              Ví:{" "}
              <span className="font-bold text-slate-700">
                {customer.points_balance.toLocaleString("vi-VN")} điểm
              </span>
              {customer.current_tier_name && (
                <span> · {customer.current_tier_name}</span>
              )}
            </p>
          )}
        </div>
      </div>
      <button
        type="button"
        onClick={onReset}
        className="text-[12px] font-bold text-emerald-700 underline"
      >
        Đổi khách
      </button>
    </div>
  );
}
