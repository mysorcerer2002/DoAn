"use client";

import {
  Ban,
  Check,
  CheckCircle2,
  Clock,
  Loader2,
  Store,
  X,
} from "lucide-react";
import { useState } from "react";

import { StatCard } from "@/components/ui/stat-card";
import { TabPills, type TabPillItem } from "@/components/ui/tab-pills";
import {
  useAdminTenants,
  useApproveTenant,
} from "@/lib/hooks/use-merchant";
import type { TenantResponse } from "@/types/merchant";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const TABS: TabPillItem[] = [
  { id: "all", label: "Tất cả" },
  { id: "pending", label: "Chờ duyệt" },
  { id: "active", label: "Đang hoạt động" },
  { id: "suspended", label: "Tạm dừng" },
];

export default function AdminTenantsPage() {
  const [activeTab, setActiveTab] = useState<string>("all");
  // Fetch full list 1 lần để tính stats + filter client-side theo tab
  const { data: allTenants, isLoading, isError } = useAdminTenants(undefined);
  const approveMutation = useApproveTenant();

  const stats = {
    total: allTenants?.length ?? 0,
    pending: allTenants?.filter((t) => t.status === "pending").length ?? 0,
    active: allTenants?.filter((t) => t.status === "active").length ?? 0,
    suspended: allTenants?.filter((t) => t.status === "suspended").length ?? 0,
  };

  const tenants =
    activeTab === "all"
      ? allTenants
      : allTenants?.filter((t) => t.status === activeTab);

  const handleApprove = async (id: number, approve: boolean) => {
    const actionText = approve ? "duyệt" : "từ chối";
    if (!confirm(`Xác nhận ${actionText} đối tác này?`)) return;
    try {
      await approveMutation.mutateAsync({ id, approve });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail ?? `Không thể ${actionText} đối tác`);
    }
  };

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Hệ thống / Đối tác</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Quản lý đối tác
          </h1>
        </div>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon={Store}
          label="Tổng đối tác"
          value={stats.total.toString()}
          tone="indigo"
        />
        <StatCard
          icon={Clock}
          label="Chờ duyệt"
          value={stats.pending.toString()}
          tone="amber"
        />
        <StatCard
          icon={CheckCircle2}
          label="Đang hoạt động"
          value={stats.active.toString()}
          tone="green"
        />
        <StatCard
          icon={Ban}
          label="Tạm dừng"
          value={stats.suspended.toString()}
          tone="red"
        />
      </section>

      <TabPills
        items={TABS}
        activeId={activeTab}
        onChange={setActiveTab}
        variant="pills"
        className="mt-5"
      />

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <div className="p-6 text-center text-red-600">
            Không tải được danh sách đối tác
          </div>
        ) : tenants?.length === 0 ? (
          <div className="p-16 text-center">
            <Store className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">Không có đối tác</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr className="text-left text-[11px] font-bold uppercase text-slate-500">
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Đối tác</th>
                <th className="px-4 py-3">Slug</th>
                <th className="px-4 py-3">Ngày đăng ký</th>
                <th className="px-4 py-3 text-center">Trạng thái</th>
                <th className="px-4 py-3 text-right">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {tenants?.map((t: TenantResponse, idx) => (
                <tr
                  key={t.id}
                  className="border-b border-slate-50 last:border-b-0 hover:bg-slate-50/50"
                >
                  <td className="px-4 py-3 text-[12px] text-slate-400">
                    {idx + 1}
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-[13px] font-bold text-slate-800">
                        {t.name}
                      </p>
                      {t.description && (
                        <p className="truncate text-[11px] text-slate-400">
                          {t.description}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-[12px] text-slate-500">
                    {t.slug}
                  </td>
                  <td className="px-4 py-3 text-[12px] text-slate-500">
                    {formatDate(t.created_at)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={t.status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {t.status === "pending" && (
                        <>
                          <button
                            type="button"
                            onClick={() => handleApprove(t.id, true)}
                            disabled={approveMutation.isPending}
                            className="flex items-center gap-1 rounded-lg bg-emerald-50 px-3 py-1.5 text-[11px] font-bold text-emerald-600 hover:bg-emerald-100 disabled:opacity-60"
                          >
                            <Check className="h-3 w-3" />
                            Duyệt
                          </button>
                          <button
                            type="button"
                            onClick={() => handleApprove(t.id, false)}
                            disabled={approveMutation.isPending}
                            className="flex items-center gap-1 rounded-lg bg-red-50 px-3 py-1.5 text-[11px] font-bold text-red-600 hover:bg-red-100 disabled:opacity-60"
                          >
                            <X className="h-3 w-3" />
                            Từ chối
                          </button>
                        </>
                      )}
                      {t.status === "active" && (
                        <button
                          type="button"
                          onClick={() => handleApprove(t.id, false)}
                          disabled={approveMutation.isPending}
                          className="flex items-center gap-1 rounded-lg bg-amber-50 px-3 py-1.5 text-[11px] font-bold text-amber-700 hover:bg-amber-100 disabled:opacity-60"
                        >
                          <Ban className="h-3 w-3" />
                          Tạm dừng
                        </button>
                      )}
                      {t.status === "suspended" && (
                        <button
                          type="button"
                          onClick={() => handleApprove(t.id, true)}
                          disabled={approveMutation.isPending}
                          className="flex items-center gap-1 rounded-lg bg-emerald-50 px-3 py-1.5 text-[11px] font-bold text-emerald-600 hover:bg-emerald-100 disabled:opacity-60"
                        >
                          <Check className="h-3 w-3" />
                          Kích hoạt lại
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<
    string,
    { label: string; className: string }
  > = {
    pending: {
      label: "Chờ duyệt",
      className: "bg-amber-50 text-amber-700",
    },
    active: {
      label: "Đang hoạt động",
      className: "bg-emerald-50 text-emerald-600",
    },
    suspended: {
      label: "Tạm dừng",
      className: "bg-red-50 text-red-600",
    },
  };
  const cfg = config[status] ?? {
    label: status,
    className: "bg-slate-100 text-slate-600",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-bold ${cfg.className}`}
    >
      {cfg.label}
    </span>
  );
}
