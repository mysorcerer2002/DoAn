"use client";

import { useState } from "react";
import { Loader2, ShieldAlert, AlertCircle } from "lucide-react";
import { useAdminAuditLogs } from "@/lib/hooks/use-admin-audit-logs";
import type { AuditLogResponse, AuditAction } from "@/types/audit";

const PAGE_SIZE = 50;

const ACTION_LABELS: Record<AuditAction, string> = {
  user_lock: "Khoá tài khoản",
  user_unlock: "Mở khoá tài khoản",
  user_role_change: "Đổi vai trò",
  partner_approve: "Duyệt shop",
  partner_reject: "Từ chối shop",
  partner_suspend: "Đình chỉ shop",
  partner_unsuspend: "Khôi phục shop",
};

const ACTION_COLORS: Record<AuditAction, string> = {
  user_lock: "bg-red-100 text-red-700",
  user_unlock: "bg-green-100 text-green-700",
  user_role_change: "bg-blue-100 text-blue-700",
  partner_approve: "bg-emerald-100 text-emerald-700",
  partner_reject: "bg-orange-100 text-orange-700",
  partner_suspend: "bg-red-100 text-red-700",
  partner_unsuspend: "bg-green-100 text-green-700",
};

function ActionBadge({ action }: { action: string }) {
  const label = ACTION_LABELS[action as AuditAction] ?? action;
  const color = ACTION_COLORS[action as AuditAction] ?? "bg-gray-100 text-gray-700";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${color}`}>
      {label}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function SnapshotDiff({
  before,
  after,
}: {
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
}) {
  if (!before && !after) return <span className="text-gray-400 text-xs">—</span>;
  const keys = Array.from(
    new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})])
  );
  return (
    <div className="text-xs space-y-0.5">
      {keys.map((k) => {
        const bv = String(before?.[k] ?? "—");
        const av = String(after?.[k] ?? "—");
        const changed = bv !== av;
        return (
          <div key={k} className="flex gap-1">
            <span className="text-gray-500 w-28 shrink-0">{k}:</span>
            {changed ? (
              <>
                <span className="line-through text-red-500">{bv}</span>
                <span className="text-gray-400">→</span>
                <span className="text-green-600">{av}</span>
              </>
            ) : (
              <span className="text-gray-600">{bv}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function AdminAuditLogsPage() {
  const [page, setPage] = useState(0);
  const [filterAction, setFilterAction] = useState<string>("");
  const [filterTargetType, setFilterTargetType] = useState<"" | "user" | "partner">("");

  const { data, isLoading, isError } = useAdminAuditLogs({
    action: filterAction || undefined,
    target_type: (filterTargetType as "user" | "partner") || undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });

  const items: AuditLogResponse[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  function resetPage() {
    setPage(0);
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-4">
      <div className="flex items-center gap-2">
        <ShieldAlert className="h-5 w-5 text-indigo-600" />
        <h1 className="text-xl font-bold">Nhật ký kiểm toán quản trị</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-white"
          value={filterTargetType}
          onChange={(e) => {
            setFilterTargetType(e.target.value as "" | "user" | "partner");
            resetPage();
          }}
        >
          <option value="">Tất cả đối tượng</option>
          <option value="user">Người dùng</option>
          <option value="partner">Shop</option>
        </select>

        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-white"
          value={filterAction}
          onChange={(e) => {
            setFilterAction(e.target.value);
            resetPage();
          }}
        >
          <option value="">Tất cả hành động</option>
          {(Object.keys(ACTION_LABELS) as AuditAction[]).map((a) => (
            <option key={a} value={a}>
              {ACTION_LABELS[a]}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin h-6 w-6 text-gray-400" />
        </div>
      )}

      {isError && (
        <div className="flex items-center gap-2 text-red-600 py-4">
          <AlertCircle className="h-4 w-4" />
          <span>Không tải được dữ liệu.</span>
        </div>
      )}

      {!isLoading && !isError && (
        <>
          <div className="text-sm text-gray-500">
            {total} bản ghi
          </div>

          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3">Thời gian</th>
                  <th className="px-4 py-3">Hành động</th>
                  <th className="px-4 py-3">Admin thực hiện</th>
                  <th className="px-4 py-3">Đối tượng</th>
                  <th className="px-4 py-3">Lý do</th>
                  <th className="px-4 py-3">Thay đổi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-400">
                      Chưa có bản ghi nào.
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-gray-500">
                        {formatDate(item.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <ActionBadge action={item.action} />
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {item.actor_email ?? `#${item.actor_user_id}`}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-gray-700">
                          {item.target_label ?? `${item.target_type} #${item.target_id}`}
                        </div>
                        <div className="text-[11px] text-gray-400">
                          {item.target_type === "user" ? "Người dùng" : "Shop"}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-[200px]">
                        {item.reason ?? <span className="text-gray-300 italic">không có</span>}
                      </td>
                      <td className="px-4 py-3">
                        <SnapshotDiff
                          before={item.before_snapshot}
                          after={item.after_snapshot}
                        />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center gap-2 justify-end">
              <button
                className="px-3 py-1 rounded border text-sm disabled:opacity-40"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                ← Trước
              </button>
              <span className="text-sm text-gray-600">
                Trang {page + 1} / {totalPages}
              </span>
              <button
                className="px-3 py-1 rounded border text-sm disabled:opacity-40"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Sau →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
