"use client";

import {
  Check,
  Crown,
  Delete,
  Loader2,
  Phone,
  QrCode,
  Sparkles,
  Tag,
} from "lucide-react";
import { useState } from "react";

import { useCreateTransaction } from "@/lib/hooks/use-merchant";
import type { TransactionWithMemberResponse } from "@/types/merchant";

type PadKey =
  | "0"
  | "1"
  | "2"
  | "3"
  | "4"
  | "5"
  | "6"
  | "7"
  | "8"
  | "9"
  | "000"
  | "del";

const numberPad: readonly PadKey[] = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "000",
  "0",
  "del",
];

function formatVnd(n: string): string {
  if (n === "") return "0 ₫";
  const num = Number(n);
  if (Number.isNaN(num)) return "0 ₫";
  return num.toLocaleString("vi-VN") + " ₫";
}

export default function PosNewTransactionPage() {
  const [mode, setMode] = useState<"phone" | "qr">("phone");
  const [phone, setPhone] = useState("");
  const [amount, setAmount] = useState("");
  const [voucherCode, setVoucherCode] = useState("");
  const [note, setNote] = useState("");
  const [result, setResult] = useState<TransactionWithMemberResponse | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const createTxn = useCreateTransaction();

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
    if (!phone.trim() || !amount.trim() || Number(amount) <= 0) {
      setError("Vui lòng nhập số điện thoại và số tiền hợp lệ");
      return;
    }
    try {
      const res = await createTxn.mutateAsync({
        phone: phone.trim(),
        gross_amount: Number(amount),
        voucher_code: voucherCode.trim() || null,
        note: note.trim() || null,
      });
      setResult(res.data);
      setAmount("");
      setVoucherCode("");
      setNote("");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? "Lỗi tạo giao dịch");
    }
  };

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Giao dịch / Tạo mới</p>
        <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
          Tạo giao dịch tích điểm
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Nhập thông tin để tích điểm cho khách hàng
        </p>
      </header>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-5">
        {/* Form 60% on desktop */}
        <section className="space-y-5 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-3">
          <div>
            <h2 className="font-headline text-[16px] font-bold text-slate-800">
              Khách hàng
            </h2>
            <div className="mt-3 flex w-fit items-center gap-1 rounded-full bg-slate-100 p-1">
              <button
                type="button"
                onClick={() => setMode("phone")}
                className={
                  mode === "phone"
                    ? "flex items-center gap-1.5 rounded-full bg-brand-indigo px-4 py-2 text-[12px] font-bold text-white shadow"
                    : "flex items-center gap-1.5 rounded-full px-4 py-2 text-[12px] font-medium text-slate-500"
                }
              >
                <Phone className="h-3.5 w-3.5" />
                Số điện thoại
              </button>
              <button
                type="button"
                onClick={() => setMode("qr")}
                className={
                  mode === "qr"
                    ? "flex items-center gap-1.5 rounded-full bg-brand-indigo px-4 py-2 text-[12px] font-bold text-white shadow"
                    : "flex items-center gap-1.5 rounded-full px-4 py-2 text-[12px] font-medium text-slate-500"
                }
              >
                <QrCode className="h-3.5 w-3.5" />
                Quét QR
              </button>
            </div>

            {mode === "phone" ? (
              <div className="relative mt-3">
                <Phone className="pointer-events-none absolute inset-y-0 left-4 my-auto h-5 w-5 text-slate-400" />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Nhập số điện thoại khách hàng (vd: 0987654321)"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-4 pl-12 pr-3 text-[16px] font-medium outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>
            ) : (
              <div className="mt-3 flex h-20 items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 text-[13px] text-slate-500">
                Chức năng quét QR sẽ có trong phiên bản sau
              </div>
            )}
            <p className="mt-2 flex items-center gap-1 text-[11px] text-slate-400">
              <Sparkles className="h-3 w-3 text-brand-orange" />
              Khách chưa có tài khoản? Hệ thống tự động tạo mới
            </p>
          </div>

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
                  className="flex h-14 items-center justify-center rounded-xl bg-indigo-50 text-[22px] font-bold text-brand-indigo transition-transform hover:bg-indigo-100 active:scale-95"
                >
                  {key === "del" ? <Delete className="h-5 w-5" /> : key}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-100 pt-4">
            <h2 className="font-headline text-[16px] font-bold text-slate-800">
              Voucher + Ghi chú (tuỳ chọn)
            </h2>
            <div className="mt-3 space-y-2">
              <div className="relative">
                <Tag className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={voucherCode}
                  onChange={(e) => setVoucherCode(e.target.value)}
                  placeholder="Mã voucher"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Ghi chú"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
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
                <span className="text-slate-500">Số tiền</span>
                <span className="font-medium text-slate-800">
                  {formatVnd(amount)}
                </span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-slate-500">Khách</span>
                <span className="font-medium text-slate-800">
                  {phone || "—"}
                </span>
              </li>
              {voucherCode && (
                <li className="flex items-center justify-between">
                  <span className="text-slate-500">Voucher</span>
                  <span className="font-mono text-[12px] text-brand-orange">
                    {voucherCode}
                  </span>
                </li>
              )}
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
              disabled={createTxn.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3 font-headline text-[14px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-[0.98] disabled:opacity-60"
            >
              {createTxn.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              {createTxn.isPending ? "Đang tích..." : "Xác nhận tích điểm"}
            </button>
            <button
              type="button"
              onClick={() => {
                setPhone("");
                setAmount("");
                setVoucherCode("");
                setNote("");
                setResult(null);
                setError(null);
              }}
              className="w-full rounded-xl border border-slate-200 py-3 text-[13px] font-medium text-slate-600 hover:bg-slate-50"
            >
              Huỷ / Làm mới
            </button>
          </div>
        </aside>
      </div>
    </main>
  );
}
