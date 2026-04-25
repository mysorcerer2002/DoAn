"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

import {
  usePartnerTransactionDetail,
  useUpdatePartnerTransaction,
} from "@/lib/hooks/use-partner-transactions";

const fmtMoney = (n: number | null) =>
  n === null ? "—" : n.toLocaleString("vi-VN") + " ₫";
const fmtDateTime = (iso: string) =>
  new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export function TransactionDetailSheet({
  transactionId,
  isOwner,
  open,
  onClose,
}: {
  transactionId: number | null;
  isOwner: boolean;
  open: boolean;
  onClose: () => void;
}) {
  const detailQ = usePartnerTransactionDetail(transactionId);
  const updateMut = useUpdatePartnerTransaction();

  const [receiptCode, setReceiptCode] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (detailQ.data) {
      setReceiptCode(detailQ.data.receipt_code ?? "");
      setNote(detailQ.data.note ?? "");
      setError(null);
      setSuccess(null);
    }
  }, [detailQ.data]);

  const handleSave = async () => {
    if (!transactionId) return;
    setError(null);
    setSuccess(null);
    try {
      await updateMut.mutateAsync({
        id: transactionId,
        payload: {
          receipt_code: receiptCode.trim() || null,
          note: note.trim() || null,
        },
      });
      setSuccess("Đã lưu.");
    } catch (err: unknown) {
      const e = err as { response?: { status?: number; data?: { detail?: string } } };
      const status = e?.response?.status;
      const detail = e?.response?.data?.detail;
      if (status === 409) {
        setError(detail ?? "Mã hoá đơn đã tồn tại cho đối tác này.");
      } else {
        setError(detail ?? "Lưu thất bại.");
      }
    }
  };

  const t = detailQ.data;

  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm transition-opacity ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-screen w-full max-w-md flex-col bg-white shadow-2xl transition-transform ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        aria-label="Chi tiết giao dịch"
      >
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="font-headline text-[18px] font-bold text-slate-800">
            Chi tiết giao dịch
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100"
            aria-label="Đóng"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4 text-[13px]">
          {detailQ.isLoading && (
            <p className="text-slate-500">Đang tải...</p>
          )}
          {t && (
            <div className="space-y-3">
              <InfoRow label="Thời gian" value={fmtDateTime(t.created_at)} />
              <InfoRow
                label="Khách hàng"
                value={t.membership_display_name}
              />
              <InfoRow label="Doanh thu" value={fmtMoney(t.gross_amount)} />
              <InfoRow label="Thực thu" value={fmtMoney(t.net_amount)} />
              <InfoRow
                label="Điểm đã tích"
                value={`${t.points_earned} điểm`}
              />
              <InfoRow label="Phương thức" value={t.method} />

              {isOwner ? (
                <div className="mt-5 space-y-3 border-t border-slate-100 pt-4">
                  <div>
                    <label
                      htmlFor="edit_receipt_code"
                      className="text-[12px] font-semibold text-slate-700"
                    >
                      Mã hoá đơn
                    </label>
                    <input
                      id="edit_receipt_code"
                      type="text"
                      value={receiptCode}
                      onChange={(e) => setReceiptCode(e.target.value)}
                      maxLength={50}
                      placeholder="VD: HD-00123"
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="edit_note"
                      className="text-[12px] font-semibold text-slate-700"
                    >
                      Ghi chú
                    </label>
                    <textarea
                      id="edit_note"
                      rows={3}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      maxLength={1000}
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                    />
                  </div>

                  {error && (
                    <p className="rounded-xl bg-rose-50 px-3 py-2 text-[12px] text-rose-600">
                      {error}
                    </p>
                  )}
                  {success && (
                    <p className="rounded-xl bg-emerald-50 px-3 py-2 text-[12px] text-emerald-700">
                      {success}
                    </p>
                  )}

                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={updateMut.isPending}
                    className="w-full rounded-xl bg-brand-indigo px-4 py-2.5 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-60"
                  >
                    {updateMut.isPending ? "Đang lưu..." : "Lưu"}
                  </button>
                </div>
              ) : (
                <div className="mt-5 space-y-2 border-t border-slate-100 pt-4 text-[12px] text-slate-600">
                  <div>
                    <span className="font-semibold text-slate-700">
                      Mã HĐ:
                    </span>{" "}
                    {t.receipt_code ?? "—"}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700">
                      Ghi chú:
                    </span>{" "}
                    {t.note ?? "—"}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium text-slate-800">{value}</span>
    </div>
  );
}
