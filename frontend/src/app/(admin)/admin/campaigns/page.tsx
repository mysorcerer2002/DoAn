"use client";

import { ClipboardList } from "lucide-react";
import Link from "next/link";

import { usePendingCampaigns } from "@/lib/hooks/use-admin-campaigns";

const PROGRAM_FORM_LABELS: Record<string, string> = {
  giam_gia: "Giảm giá",
  tang_kem: "Tặng kèm",
  may_rui_quay_so: "May rủi – quay số",
  may_rui_truc_tiep: "May rủi – trực tiếp",
  khach_hang_thuong_xuyen: "Khách hàng thường xuyên",
};

const TIER_LABELS: Record<string, string> = {
  none: "Không cần",
  auto: "Tự động",
  notify: "Thông báo",
  register: "Đăng ký",
  reject: "Từ chối",
};

const TIER_COLORS: Record<string, string> = {
  none: "bg-slate-100 text-slate-600",
  auto: "bg-emerald-100 text-emerald-700",
  notify: "bg-blue-100 text-blue-700",
  register: "bg-amber-100 text-amber-700",
  reject: "bg-red-100 text-red-600",
};

const FEE_LABELS: Record<string, string> = {
  none: "Không áp dụng",
  pending: "Chờ thanh toán",
  paid: "Đã thanh toán",
  waived: "Miễn phí",
};

const FEE_COLORS: Record<string, string> = {
  none: "bg-slate-100 text-slate-500",
  pending: "bg-amber-100 text-amber-700",
  paid: "bg-emerald-100 text-emerald-700",
  waived: "bg-indigo-100 text-indigo-700",
};

function fmtMoney(n: number): string {
  return n.toLocaleString("vi-VN") + "₫";
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function AdminCampaignsPage() {
  const { data: campaigns = [], isLoading } = usePendingCampaigns({ limit: 100 });

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <ClipboardList className="h-6 w-6 text-indigo-600" />
        <h1 className="text-xl font-bold text-slate-800">Hàng chờ duyệt chiến dịch</h1>
        {campaigns.length > 0 && (
          <span className="rounded-full bg-indigo-600 px-2.5 py-0.5 text-[11px] font-bold text-white">
            {campaigns.length}
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
              <th className="px-4 py-3 text-left">Hình thức</th>
              <th className="px-4 py-3 text-left">Mức duyệt</th>
              <th className="px-4 py-3 text-right">Dự toán</th>
              <th className="px-4 py-3 text-left">Phí DV</th>
              <th className="px-4 py-3 text-left">Bắt đầu</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                  Đang tải...
                </td>
              </tr>
            )}
            {!isLoading && campaigns.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                  Không có chiến dịch chờ duyệt.
                </td>
              </tr>
            )}
            {campaigns.map((c) => (
              <tr
                key={c.id}
                className="cursor-pointer hover:bg-slate-50"
              >
                <td className="px-4 py-3 text-slate-500">
                  <Link href={`/admin/campaigns/${c.id}`} className="block hover:text-indigo-600">
                    #{c.id}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <Link href={`/admin/campaigns/${c.id}`} className="block font-medium text-slate-700 hover:text-indigo-600">
                    {c.tenant_name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <Link href={`/admin/campaigns/${c.id}`} className="block text-slate-800 hover:text-indigo-600">
                    {c.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{PROGRAM_FORM_LABELS[c.program_form] ?? c.program_form}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${TIER_COLORS[c.approval_tier] ?? "bg-slate-100 text-slate-600"}`}
                  >
                    {TIER_LABELS[c.approval_tier] ?? c.approval_tier}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-700">
                  {fmtMoney(c.estimated_cost)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${FEE_COLORS[c.service_fee_status] ?? "bg-slate-100 text-slate-500"}`}
                  >
                    {FEE_LABELS[c.service_fee_status] ?? c.service_fee_status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{fmtDate(c.starts_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
