"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";

import { useOverdueReports } from "@/lib/hooks/use-admin-campaigns";

const TIER_LABELS: Record<string, string> = {
  none: "Không cần",
  auto: "Tự động",
  notify: "Thông báo",
  register: "Đăng ký",
  reject: "Từ chối",
};

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function OverdueCampaignsPage() {
  const { data: rows = [], isLoading } = useOverdueReports();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <AlertTriangle className="h-6 w-6 text-amber-500" />
        <h1 className="text-xl font-bold text-slate-800">Chiến dịch quá hạn báo cáo</h1>
        {rows.length > 0 && (
          <span className="rounded-full bg-amber-500 px-2.5 py-0.5 text-[11px] font-bold text-white">
            {rows.length}
          </span>
        )}
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-[12px] font-semibold text-slate-500 uppercase tracking-wide">
            <tr>
              <th className="px-4 py-3 text-left">ID</th>
              <th className="px-4 py-3 text-left">Shop</th>
              <th className="px-4 py-3 text-left">Tên chiến dịch</th>
              <th className="px-4 py-3 text-left">Mức duyệt</th>
              <th className="px-4 py-3 text-left">Hạn báo cáo</th>
              <th className="px-4 py-3 text-right">Quá hạn</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  Đang tải...
                </td>
              </tr>
            )}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  Không có chiến dịch nào quá hạn.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-slate-500">
                  <Link
                    href={`/admin/campaigns/${r.id}`}
                    className="hover:text-indigo-600"
                  >
                    #{r.id}
                  </Link>
                </td>
                <td className="px-4 py-3 font-medium text-slate-700">
                  <Link
                    href={`/admin/campaigns/${r.id}`}
                    className="hover:text-indigo-600"
                  >
                    {r.tenant_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-800">
                  <Link
                    href={`/admin/campaigns/${r.id}`}
                    className="hover:text-indigo-600"
                  >
                    {r.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {TIER_LABELS[r.approval_tier] ?? r.approval_tier}
                </td>
                <td className="px-4 py-3 text-slate-600">{fmtDate(r.post_report_due_at)}</td>
                <td className="px-4 py-3 text-right">
                  <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-[11px] font-bold text-red-600">
                    +{r.days_overdue} ngày
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
