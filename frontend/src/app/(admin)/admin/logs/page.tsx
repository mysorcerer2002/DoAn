"use client";

import { useState, useEffect, useRef } from "react";
import { Loader2, FileText, AlertCircle } from "lucide-react";
import { TabPills } from "@/components/ui/tab-pills";
import { useAdminLoginLogs, useAdminPointAdjustments } from "@/lib/hooks/useAdminLogs";

type TabId = "login" | "adjustments";

const TABS = [
  { id: "login" as TabId, label: "Đăng nhập" },
  { id: "adjustments" as TabId, label: "Điều chỉnh điểm" },
];

function Badge({ success }: { success: boolean }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
        success
          ? "bg-green-100 text-green-700"
          : "bg-red-100 text-red-700"
      }`}
    >
      {success ? "OK" : "Fail"}
    </span>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  return (
    <span
      className={`font-bold ${delta >= 0 ? "text-green-600" : "text-red-600"}`}
    >
      {delta >= 0 ? `+${delta}` : delta}
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

// Simple debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export default function AdminLogsPage() {
  const [tab, setTab] = useState<TabId>("login");

  // Login filters
  const [identifierInput, setIdentifierInput] = useState("");
  const [successFilter, setSuccessFilter] = useState<"all" | "true" | "false">("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const debouncedIdentifier = useDebounce(identifierInput, 500);

  const loginFilters = {
    identifier: debouncedIdentifier || undefined,
    success:
      successFilter === "all" ? undefined : successFilter === "true",
    from: fromDate || undefined,
    to: toDate || undefined,
    limit: 50,
  };

  const { data: loginData, isLoading: loginLoading } = useAdminLoginLogs(loginFilters);
  const { data: adjData, isLoading: adjLoading } = useAdminPointAdjustments({ limit: 50 });

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Hệ thống / Nhật ký</p>
        <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
          Nhật ký hệ thống
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Lịch sử đăng nhập và điều chỉnh điểm toàn platform
        </p>
      </header>

      <div className="mt-6">
        <TabPills
          items={TABS}
          activeId={tab}
          onChange={(id) => setTab(id as TabId)}
          variant="underline"
        />
      </div>

      {tab === "login" && (
        <section className="mt-4">
          {/* Filters */}
          <div className="mb-4 flex flex-wrap gap-3">
            <input
              type="text"
              placeholder="Tìm identifier (email/SĐT)..."
              value={identifierInput}
              onChange={(e) => setIdentifierInput(e.target.value)}
              className="rounded-lg border border-slate-200 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo w-56"
            />
            <select
              value={successFilter}
              onChange={(e) =>
                setSuccessFilter(e.target.value as "all" | "true" | "false")
              }
              className="rounded-lg border border-slate-200 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
            >
              <option value="all">Tất cả</option>
              <option value="true">Thành công</option>
              <option value="false">Thất bại</option>
            </select>
            <input
              type="datetime-local"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="rounded-lg border border-slate-200 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
            />
            <input
              type="datetime-local"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="rounded-lg border border-slate-200 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
            />
          </div>

          {loginLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-brand-indigo" />
            </div>
          ) : !loginData?.items.length ? (
            <EmptyState message="Chưa có log đăng nhập nào" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-sm">
              <table className="w-full text-[12px]">
                <thead className="border-b border-slate-100 bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold">Thời gian</th>
                    <th className="px-4 py-3 text-left font-semibold">Identifier</th>
                    <th className="px-4 py-3 text-left font-semibold">IP</th>
                    <th className="px-4 py-3 text-left font-semibold">Trạng thái</th>
                    <th className="px-4 py-3 text-left font-semibold">Lý do lỗi</th>
                    <th className="px-4 py-3 text-left font-semibold">User Email</th>
                    <th className="px-4 py-3 text-left font-semibold max-w-[160px]">User Agent</th>
                    <th className="px-4 py-3 text-left font-semibold">ID</th>
                  </tr>
                </thead>
                <tbody>
                  {loginData.items.map((log) => (
                    <tr key={log.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-800">
                        {log.identifier}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{log.ip}</td>
                      <td className="px-4 py-3">
                        <Badge success={log.success} />
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {log.failure_reason ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {log.user_email ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-400 max-w-[160px] truncate">
                        {log.user_agent ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-400">#{log.id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="px-4 py-2 text-[11px] text-slate-400">
                Hiển thị {loginData.items.length} / {loginData.total} bản ghi
              </p>
            </div>
          )}
        </section>
      )}

      {tab === "adjustments" && (
        <section className="mt-4">
          {adjLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-brand-indigo" />
            </div>
          ) : !adjData?.items.length ? (
            <EmptyState message="Chưa có điều chỉnh điểm nào" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-sm">
              <table className="w-full text-[12px]">
                <thead className="border-b border-slate-100 bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold">Thời gian</th>
                    <th className="px-4 py-3 text-left font-semibold">User Email</th>
                    <th className="px-4 py-3 text-left font-semibold">Đối tác</th>
                    <th className="px-4 py-3 text-left font-semibold">Actor Email</th>
                    <th className="px-4 py-3 text-left font-semibold">Delta</th>
                    <th className="px-4 py-3 text-left font-semibold">Sau điều chỉnh</th>
                    <th className="px-4 py-3 text-left font-semibold">Mô tả</th>
                    <th className="px-4 py-3 text-left font-semibold">ID</th>
                  </tr>
                </thead>
                <tbody>
                  {adjData.items.map((adj) => (
                    <tr key={adj.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                        {formatDate(adj.created_at)}
                      </td>
                      <td className="px-4 py-3 text-slate-800">{adj.user_email ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{adj.partner_name ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-500">{adj.actor_email ?? "—"}</td>
                      <td className="px-4 py-3">
                        <DeltaBadge delta={adj.delta} />
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {adj.balance_after.toLocaleString("vi-VN")}
                      </td>
                      <td className="px-4 py-3 text-slate-400">{adj.description ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-400">#{adj.id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="px-4 py-2 text-[11px] text-slate-400">
                Hiển thị {adjData.items.length} / {adjData.total} bản ghi
              </p>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-100 bg-white py-16 shadow-sm">
      <FileText className="h-10 w-10 text-slate-300" />
      <p className="mt-3 text-[13px] text-slate-400">{message}</p>
    </div>
  );
}
