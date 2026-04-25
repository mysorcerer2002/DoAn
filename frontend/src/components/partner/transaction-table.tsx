"use client";

import type { TransactionListItem } from "@/types/partner";

const fmtMoney = (n: number) => n.toLocaleString("vi-VN") + " ₫";
const fmtDateTime = (iso: string) =>
  new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

export function TransactionTable({
  items,
  total,
  page,
  pageSize,
  onPageChange,
  onRowClick,
}: {
  items: TransactionListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
  onRowClick: (id: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[13px]">
          <thead className="bg-slate-50 text-[12px] font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Ngày</th>
              <th className="px-4 py-3">Mã HĐ</th>
              <th className="px-4 py-3">Khách</th>
              <th className="px-4 py-3 text-right">Thực thu</th>
              <th className="px-4 py-3 text-right">Điểm</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-slate-400"
                >
                  Chưa có giao dịch.
                </td>
              </tr>
            )}
            {items.map((t) => (
              <tr
                key={t.id}
                onClick={() => onRowClick(t.id)}
                className="cursor-pointer hover:bg-slate-50"
              >
                <td className="px-4 py-3 text-slate-700">
                  {fmtDateTime(t.created_at)}
                </td>
                <td className="px-4 py-3 font-mono text-[12px] text-slate-600">
                  {t.receipt_code || "—"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {t.membership_display_name}
                </td>
                <td className="px-4 py-3 text-right font-semibold text-slate-800">
                  {fmtMoney(t.net_amount)}
                </td>
                <td className="px-4 py-3 text-right text-slate-700">
                  {t.points_earned}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/50 px-4 py-3">
        <span className="text-[12px] text-slate-500">
          Tổng {total} giao dịch · Trang {page} / {totalPages}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page === 1}
            onClick={() => onPageChange(page - 1)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Trước
          </button>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Sau
          </button>
        </div>
      </div>
    </div>
  );
}
