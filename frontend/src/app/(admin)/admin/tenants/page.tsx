"use client";

import {
  Ban,
  Check,
  CheckCircle2,
  Clock,
  Gift,
  Globe,
  Loader2,
  MapPin,
  Megaphone,
  Phone,
  Receipt,
  Store,
  Ticket,
  TrendingUp,
  Users,
  UserSquare2,
  X,
} from "lucide-react";
import { Fragment, useMemo, useState } from "react";

import { StatCard } from "@/components/ui/stat-card";
import { TabPills, type TabPillItem } from "@/components/ui/tab-pills";
import {
  useAdminTenantDetail,
  useAdminTenantMembers,
  useAdminTenantStaff,
  useAdminTenants,
  useApproveTenant,
} from "@/lib/hooks/use-partner";
import type {
  AdminPartnerListRow,
  AdminPartnerMemberRow,
  AdminPartnerStaffRow,
  PartnerDetailResponse,
} from "@/types/partner";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatNumber(n: number | null | undefined): string {
  return (n ?? 0).toLocaleString("vi-VN");
}

function formatCurrency(n: number | null | undefined): string {
  return `${formatNumber(n)}₫`;
}

const CATEGORY_LABEL: Record<string, string> = {
  cafe: "Cà phê",
  food: "Ẩm thực",
  retail: "Bán lẻ",
  beauty: "Làm đẹp",
  other: "Khác",
};

const TABS: TabPillItem[] = [
  { id: "all", label: "Tất cả" },
  { id: "pending", label: "Chờ duyệt" },
  { id: "active", label: "Đang hoạt động" },
  { id: "suspended", label: "Tạm dừng" },
];

export default function AdminTenantsPage() {
  const [activeTab, setActiveTab] = useState<string>("all");
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const { data: allTenants, isLoading, isError } = useAdminTenants(undefined);
  const approveMutation = useApproveTenant();

  const stats = useMemo(
    () => ({
      total: allTenants?.length ?? 0,
      pending: allTenants?.filter((t) => t.status === "pending").length ?? 0,
      active: allTenants?.filter((t) => t.status === "active").length ?? 0,
      suspended:
        allTenants?.filter((t) => t.status === "suspended").length ?? 0,
    }),
    [allTenants],
  );

  const tenants =
    activeTab === "all"
      ? allTenants
      : allTenants?.filter((t) => t.status === activeTab);

  const handleApprove = async (
    id: number,
    approve: boolean,
    event?: React.MouseEvent,
  ) => {
    event?.stopPropagation();
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
          <p className="mt-1 text-[13px] text-slate-500">
            Nhấp vào một dòng để xem chi tiết, khách hàng & nhân viên của đối tác.
          </p>
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
            <table className="w-full min-w-[1100px]">
              <thead className="border-b border-slate-100 bg-slate-50">
                <tr className="text-left text-[11px] font-bold uppercase text-slate-500">
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Đối tác</th>
                  <th className="px-4 py-3">Chủ sở hữu</th>
                  <th className="px-4 py-3 text-right">Khách</th>
                  <th className="px-4 py-3 text-right">NV</th>
                  <th className="px-4 py-3 text-right">Hoạt động 30 ngày</th>
                  <th className="px-4 py-3 text-center">Trạng thái</th>
                  <th className="px-4 py-3 text-right">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {tenants?.map((t: AdminPartnerListRow, idx) => (
                  <tr
                    key={t.id}
                    onClick={() => setSelectedTenantId(t.id)}
                    className="cursor-pointer border-b border-slate-50 last:border-b-0 hover:bg-indigo-50/40"
                  >
                    <td className="px-4 py-3 text-[12px] text-slate-400">
                      {idx + 1}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-indigo-50 text-indigo-500">
                          {t.logo_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={t.logo_url}
                              alt=""
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <Store className="h-4 w-4" />
                          )}
                        </div>
                        <div>
                          <p className="text-[13px] font-bold text-slate-800">
                            {t.name}
                          </p>
                          <p className="font-mono text-[11px] text-slate-400">
                            {t.slug}
                            {" · "}
                            {CATEGORY_LABEL[t.category] ?? t.category}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-[12px] font-semibold text-slate-700">
                          {t.owner_name ?? "—"}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {t.owner_email ?? "—"}
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-[13px] font-semibold text-slate-700 tabular-nums">
                      {formatNumber(t.active_member_count)}
                    </td>
                    <td className="px-4 py-3 text-right text-[13px] font-semibold text-slate-700 tabular-nums">
                      {formatNumber(t.staff_count)}
                    </td>
                    <td className="px-4 py-3 text-right text-[13px] font-semibold text-emerald-600 tabular-nums">
                      {formatNumber(t.active_member_count_30d)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div
                        className="flex items-center justify-end gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {t.status === "pending" && (
                          <Fragment>
                            <button
                              type="button"
                              onClick={(e) => handleApprove(t.id, true, e)}
                              disabled={approveMutation.isPending}
                              className="flex items-center gap-1 rounded-lg bg-emerald-50 px-3 py-1.5 text-[11px] font-bold text-emerald-600 hover:bg-emerald-100 disabled:opacity-60"
                            >
                              <Check className="h-3 w-3" />
                              Duyệt
                            </button>
                            <button
                              type="button"
                              onClick={(e) => handleApprove(t.id, false, e)}
                              disabled={approveMutation.isPending}
                              className="flex items-center gap-1 rounded-lg bg-red-50 px-3 py-1.5 text-[11px] font-bold text-red-600 hover:bg-red-100 disabled:opacity-60"
                            >
                              <X className="h-3 w-3" />
                              Từ chối
                            </button>
                          </Fragment>
                        )}
                        {t.status === "active" && (
                          <button
                            type="button"
                            onClick={(e) => handleApprove(t.id, false, e)}
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
                            onClick={(e) => handleApprove(t.id, true, e)}
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

      {selectedTenantId !== null && (
        <TenantDetailModal
          tenantId={selectedTenantId}
          onClose={() => setSelectedTenantId(null)}
        />
      )}
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: "Chờ duyệt", className: "bg-amber-50 text-amber-700" },
    active: {
      label: "Đang hoạt động",
      className: "bg-emerald-50 text-emerald-600",
    },
    suspended: { label: "Tạm dừng", className: "bg-red-50 text-red-600" },
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

// ==================== Detail Modal ====================

type DetailTab = "overview" | "members" | "staff";

function TenantDetailModal({
  tenantId,
  onClose,
}: {
  tenantId: number;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<DetailTab>("overview");
  const { data: detail, isLoading } = useAdminTenantDetail(tenantId);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-xl bg-indigo-50 text-indigo-500">
              {detail?.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={detail.logo_url}
                  alt=""
                  className="h-full w-full object-cover"
                />
              ) : (
                <Store className="h-5 w-5" />
              )}
            </div>
            <div>
              <h2 className="font-headline text-[20px] font-bold text-slate-800">
                {detail?.name ?? "Đang tải..."}
              </h2>
              <div className="mt-0.5 flex items-center gap-2">
                {detail && <StatusBadge status={detail.status} />}
                {detail && (
                  <span className="text-[11px] text-slate-400">
                    {CATEGORY_LABEL[detail.category] ?? detail.category} · /
                    {detail.slug}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="flex gap-1 border-b border-slate-100 px-6 pt-3">
          <TabButton
            active={tab === "overview"}
            onClick={() => setTab("overview")}
          >
            Tổng quan
          </TabButton>
          <TabButton
            active={tab === "members"}
            onClick={() => setTab("members")}
          >
            Khách hàng {detail ? `(${detail.member_count})` : ""}
          </TabButton>
          <TabButton active={tab === "staff"} onClick={() => setTab("staff")}>
            Nhân viên {detail ? `(${detail.staff_count})` : ""}
          </TabButton>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          {isLoading || !detail ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
            </div>
          ) : tab === "overview" ? (
            <OverviewTab detail={detail} />
          ) : tab === "members" ? (
            <MembersTab tenantId={tenantId} />
          ) : (
            <StaffTab tenantId={tenantId} />
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`-mb-px border-b-2 px-3 py-2 text-[13px] font-semibold transition ${
        active
          ? "border-brand-indigo text-brand-indigo"
          : "border-transparent text-slate-500 hover:text-slate-700"
      }`}
    >
      {children}
    </button>
  );
}

function OverviewTab({ detail }: { detail: PartnerDetailResponse }) {
  return (
    <div className="space-y-5">
      <section>
        <h3 className="mb-2 text-[11px] font-bold uppercase text-slate-400">
          Thống kê kinh doanh
        </h3>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <MetricTile
            icon={Users}
            label="Khách hàng"
            value={`${formatNumber(detail.active_member_count)} / ${formatNumber(detail.member_count)}`}
            hint="đang hoạt động / tổng"
          />
          <MetricTile
            icon={UserSquare2}
            label="Nhân viên"
            value={formatNumber(detail.staff_count)}
          />
          <MetricTile
            icon={Receipt}
            label="Giao dịch"
            value={formatNumber(detail.transaction_count)}
          />
          <MetricTile
            icon={TrendingUp}
            label="Tổng doanh thu"
            value={formatCurrency(detail.total_revenue)}
            tone="emerald"
          />
          <MetricTile
            icon={Megaphone}
            label="Chiến dịch"
            value={`${formatNumber(detail.active_campaign_count)} / ${formatNumber(detail.campaign_count)}`}
            hint="đang chạy / tổng"
          />
          <MetricTile
            icon={Gift}
            label="Phần thưởng"
            value={formatNumber(detail.reward_count)}
          />
          <MetricTile
            icon={Ticket}
            label="Voucher phát hành"
            value={formatNumber(detail.voucher_count)}
          />
          <MetricTile
            icon={Gift}
            label="Đổi thưởng"
            value={formatNumber(detail.redemption_count)}
          />
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-[11px] font-bold uppercase text-slate-400">
          Chủ sở hữu
        </h3>
        <div className="rounded-xl border border-slate-100 bg-slate-50/50 px-4 py-3">
          <p className="text-[14px] font-bold text-slate-800">
            {detail.owner_name ?? "(Chưa đặt tên)"}
          </p>
          <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-[12px] text-slate-500">
            {detail.owner_email && (
              <span>{detail.owner_email}</span>
            )}
            {detail.owner_phone && (
              <span className="flex items-center gap-1">
                <Phone className="h-3 w-3" />
                {detail.owner_phone}
              </span>
            )}
          </div>
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-[11px] font-bold uppercase text-slate-400">
          Thông tin liên hệ
        </h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <InfoRow
            icon={Phone}
            label="Điện thoại"
            value={detail.contact_phone}
          />
          <InfoRow
            icon={Phone}
            label="Email"
            value={detail.contact_email}
          />
          <InfoRow
            icon={MapPin}
            label="Địa chỉ"
            value={detail.address}
            className="md:col-span-2"
          />
          <InfoRow
            icon={Globe}
            label="Website"
            value={detail.website}
            isLink
          />
          <InfoRow
            icon={Clock}
            label="Giờ mở cửa"
            value={detail.business_hours}
          />
          <InfoRow icon={Receipt} label="Mã số thuế" value={detail.tax_code} />
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-[11px] font-bold uppercase text-slate-400">
          Mô tả
        </h3>
        <p className="text-[13px] text-slate-600">
          {detail.description || "(chưa có mô tả)"}
        </p>
      </section>

      <section className="grid grid-cols-2 gap-3 text-[12px] text-slate-500">
        <div>
          <p className="text-[11px] font-bold uppercase text-slate-400">
            Ngày đăng ký
          </p>
          <p className="mt-1">{formatDate(detail.created_at)}</p>
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase text-slate-400">
            Ngày kích hoạt
          </p>
          <p className="mt-1">
            {detail.activated_at ? formatDate(detail.activated_at) : "—"}
          </p>
        </div>
      </section>
    </div>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  hint,
  tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint?: string;
  tone?: "emerald";
}) {
  const valueClass = tone === "emerald" ? "text-emerald-600" : "text-slate-800";
  return (
    <div className="rounded-xl border border-slate-100 bg-white px-3 py-3 shadow-sm">
      <div className="flex items-center gap-2 text-slate-400">
        <Icon className="h-4 w-4" />
        <p className="text-[11px] font-bold uppercase">{label}</p>
      </div>
      <p className={`mt-1.5 text-[18px] font-bold tabular-nums ${valueClass}`}>
        {value}
      </p>
      {hint && (
        <p className="mt-0.5 text-[10px] text-slate-400">{hint}</p>
      )}
    </div>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
  isLink,
  className = "",
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null;
  isLink?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`flex items-start gap-3 rounded-xl border border-slate-100 px-3 py-2 ${className}`}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-bold uppercase text-slate-400">
          {label}
        </p>
        {value ? (
          isLink ? (
            <a
              href={value.startsWith("http") ? value : `https://${value}`}
              target="_blank"
              rel="noopener noreferrer"
              className="break-all text-[13px] text-brand-indigo hover:underline"
            >
              {value}
            </a>
          ) : (
            <p className="break-words text-[13px] text-slate-700">{value}</p>
          )
        ) : (
          <p className="text-[13px] text-slate-300">—</p>
        )}
      </div>
    </div>
  );
}

function MembersTab({ tenantId }: { tenantId: number }) {
  const { data, isLoading } = useAdminTenantMembers(tenantId, { limit: 100 });

  if (isLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-indigo" />
      </div>
    );
  }

  if (!data?.length) {
    return (
      <div className="py-12 text-center">
        <Users className="mx-auto h-10 w-10 text-slate-300" />
        <p className="mt-2 text-[13px] text-slate-500">
          Chưa có khách hàng nào.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[600px]">
        <thead className="border-b border-slate-100 text-[11px] font-bold uppercase text-slate-500">
          <tr>
            <th className="py-2 text-left">Khách hàng</th>
            <th className="py-2 text-left">Hạng</th>
            <th className="py-2 text-right">Điểm hiện có</th>
            <th className="py-2 text-right">Đã tích lũy</th>
            <th className="py-2 text-right">Tham gia</th>
          </tr>
        </thead>
        <tbody>
          {data.map((m: AdminPartnerMemberRow) => (
            <tr
              key={m.membership_id}
              className="border-b border-slate-50 last:border-b-0"
            >
              <td className="py-2">
                <p className="text-[13px] font-semibold text-slate-800">
                  {m.full_name ?? "(Khách)"}
                  {m.archived && (
                    <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500">
                      Đã rời
                    </span>
                  )}
                </p>
                <p className="text-[11px] text-slate-400">
                  {m.email ?? m.phone ?? "—"}
                </p>
              </td>
              <td className="py-2 text-[12px] text-slate-500">
                {m.current_tier_name ?? "—"}
              </td>
              <td className="py-2 text-right text-[13px] font-semibold tabular-nums text-slate-700">
                {formatNumber(m.points_balance)}
              </td>
              <td className="py-2 text-right text-[12px] tabular-nums text-slate-500">
                {formatNumber(m.total_points_earned)}
              </td>
              <td className="py-2 text-right text-[11px] text-slate-400">
                {formatDate(m.joined_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StaffTab({ tenantId }: { tenantId: number }) {
  const { data, isLoading } = useAdminTenantStaff(tenantId);

  if (isLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-indigo" />
      </div>
    );
  }

  if (!data?.length) {
    return (
      <div className="py-12 text-center">
        <UserSquare2 className="mx-auto h-10 w-10 text-slate-300" />
        <p className="mt-2 text-[13px] text-slate-500">Chưa có nhân viên.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.map((s: AdminPartnerStaffRow) => (
        <div
          key={s.user_id}
          className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3"
        >
          <div>
            <p className="text-[13px] font-semibold text-slate-800">
              {s.full_name ?? "(Chưa có tên)"}
            </p>
            <p className="text-[11px] text-slate-400">
              {s.email ?? s.phone ?? "—"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                s.role === "owner"
                  ? "bg-indigo-50 text-indigo-600"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {s.role === "owner" ? "Chủ shop" : "Nhân viên"}
            </span>
            {!s.is_active && (
              <span className="rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-bold text-red-600">
                Đã khóa
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
