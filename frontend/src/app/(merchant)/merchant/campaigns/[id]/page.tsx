"use client";

import {
  ArrowLeft,
  BadgeCheck,
  BadgePercent,
  CalendarDays,
  CheckCircle2,
  Clock,
  FileText,
  Gift,
  Loader2,
  Percent,
  ReceiptText,
  ShieldCheck,
  Target,
  TrendingUp,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import {
  useCampaignDetail,
  useCampaignRoi,
} from "@/lib/hooks/use-merchant";
import {
  useAuthorizations,
  useCampaignServiceFees,
} from "@/lib/hooks/use-merchant-enroll";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatCurrency(n: number): string {
  return `${n.toLocaleString("vi-VN")}₫`;
}

function campaignStatus(
  starts_at: string,
  ends_at: string,
): "running" | "upcoming" | "ended" {
  const now = Date.now();
  const start = new Date(starts_at).getTime();
  const end = new Date(ends_at).getTime();
  if (now < start) return "upcoming";
  if (now > end) return "ended";
  return "running";
}

const STATUS_CONFIG = {
  running: {
    label: "Đang chạy",
    className: "bg-emerald-500 text-white",
    icon: CheckCircle2,
  },
  upcoming: {
    label: "Sắp diễn ra",
    className: "bg-amber-500 text-white",
    icon: Clock,
  },
  ended: {
    label: "Đã kết thúc",
    className: "bg-slate-600 text-white",
    icon: FileText,
  },
} as const;

const SOURCE_LABEL: Record<string, string> = {
  manual: "Thủ công",
  birthday: "Sinh nhật",
  signup: "Đăng ký mới",
};

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const {
    data: campaign,
    isLoading,
    isError,
  } = useCampaignDetail(Number.isFinite(id) ? id : null);
  const { data: roi } = useCampaignRoi(Number.isFinite(id) ? id : null);
  const { data: authorizations } = useAuthorizations();
  const { data: serviceFees } = useCampaignServiceFees(
    Number.isFinite(id) ? id : null,
  );

  // Tìm uỷ quyền liên kết với campaign này — ưu tiên còn hiệu lực, sau đó mới nhất
  const linkedAuth = authorizations
    ?.filter((a) => a.campaign_id === id)
    .sort((a, b) => {
      // Active first
      if (!a.revoked_at && b.revoked_at) return -1;
      if (a.revoked_at && !b.revoked_at) return 1;
      // Then most recent
      return new Date(b.signed_at).getTime() - new Date(a.signed_at).getTime();
    })[0];

  if (isLoading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }
  if (isError || !campaign) {
    return (
      <main className="px-4 py-8 md:px-8">
        <Link
          href="/merchant/campaigns"
          className="inline-flex items-center gap-1 text-[13px] text-brand-indigo"
        >
          <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
        </Link>
        <p className="mt-6 text-center text-red-600">
          Không tìm thấy chiến dịch.
        </p>
      </main>
    );
  }

  const status = campaignStatus(campaign.starts_at, campaign.ends_at);
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  const issued = roi?.vouchers_issued ?? campaign.issued_count;
  const used = roi?.vouchers_used ?? campaign.used_count;
  const totalDiscount =
    roi?.total_discount_amount ?? campaign.total_discount_amount;
  const totalRevenue =
    roi?.total_revenue_from_voucher_txns ??
    campaign.total_revenue_from_voucher_txns;

  const usageRate = issued > 0 ? Math.round((used / issued) * 100) : 0;
  const roiRate =
    totalDiscount > 0
      ? Math.round((totalRevenue / totalDiscount) * 100) / 100
      : null;

  // Ước tính ngân sách tối đa: max_issuances × mức giảm tối đa mỗi voucher
  let maxBudget: number | null = null;
  if (campaign.max_issuances) {
    if (campaign.discount_type === "percent") {
      if (campaign.max_discount) {
        maxBudget = campaign.max_issuances * campaign.max_discount;
      }
    } else {
      maxBudget = campaign.max_issuances * campaign.discount_value;
    }
  }

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <Link
        href="/merchant/campaigns"
        className="inline-flex items-center gap-1 text-[12px] text-slate-500 hover:text-brand-indigo"
      >
        <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
      </Link>

      <header className="mt-3 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Marketing / Chiến dịch</p>
          <h1 className="mt-1 font-headline text-[28px] font-bold text-slate-800 md:text-[32px]">
            {campaign.name}
          </h1>
          {campaign.description && (
            <p className="mt-2 max-w-2xl text-[13px] text-slate-600">
              {campaign.description}
            </p>
          )}
        </div>
        <span
          className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-bold ${statusConfig.className}`}
        >
          <StatusIcon className="h-3.5 w-3.5" />
          {statusConfig.label}
        </span>
      </header>

      {/* Metrics */}
      <section className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <MetricTile
          icon={Gift}
          label="Đã phát"
          value={issued.toString()}
          hint={
            campaign.max_issuances
              ? `/${campaign.max_issuances} tối đa`
              : "không giới hạn"
          }
          tone="indigo"
        />
        <MetricTile
          icon={BadgeCheck}
          label="Đã đổi"
          value={used.toString()}
          hint={`${usageRate}% tỉ lệ sử dụng`}
          tone="green"
        />
        <MetricTile
          icon={Wallet}
          label="Tổng chi phí giảm giá"
          value={formatCurrency(totalDiscount)}
          hint={
            maxBudget !== null
              ? `Ngân sách tối đa: ${formatCurrency(maxBudget)}`
              : "theo thực tế đã dùng"
          }
          tone="rose"
        />
        <MetricTile
          icon={TrendingUp}
          label="Doanh thu voucher"
          value={formatCurrency(totalRevenue)}
          hint={roiRate !== null ? `ROI ×${roiRate}` : "chưa có đơn dùng"}
          tone="emerald"
        />
      </section>

      {/* Budget progress */}
      {campaign.max_issuances && (
        <section className="mt-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between text-[12px] text-slate-500">
            <span>Tiến độ phát voucher</span>
            <span className="font-bold text-slate-700">
              {issued} / {campaign.max_issuances}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full bg-gradient-to-r from-brand-indigo to-brand-violet"
              style={{
                width: `${Math.min(
                  100,
                  (issued / campaign.max_issuances) * 100,
                )}%`,
              }}
            />
          </div>
        </section>
      )}

      {/* Two columns: info + rules */}
      <section className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">

          <h3 className="font-headline text-[15px] font-bold text-slate-800">
            Thông tin ưu đãi
          </h3>
          <div className="mt-3 space-y-3 text-[13px]">
            <InfoRow
              icon={campaign.discount_type === "percent" ? Percent : BadgePercent}
              label="Loại giảm giá"
              value={
                campaign.discount_type === "percent"
                  ? `Giảm ${campaign.discount_value}%`
                  : `Giảm ${formatCurrency(campaign.discount_value)}`
              }
            />
            {campaign.max_discount !== null && (
              <InfoRow
                icon={Wallet}
                label="Giảm tối đa"
                value={formatCurrency(campaign.max_discount)}
              />
            )}
            {campaign.min_order !== null && campaign.min_order > 0 && (
              <InfoRow
                icon={ReceiptText}
                label="Đơn tối thiểu"
                value={formatCurrency(campaign.min_order)}
              />
            )}
            <InfoRow
              icon={CalendarDays}
              label="Bắt đầu"
              value={formatDate(campaign.starts_at)}
            />
            <InfoRow
              icon={CalendarDays}
              label="Kết thúc"
              value={formatDate(campaign.ends_at)}
            />
            <InfoRow
              icon={Target}
              label="Nguồn"
              value={SOURCE_LABEL[campaign.source] ?? campaign.source}
            />
            {campaign.target_tier_id !== null && (
              <InfoRow
                icon={Target}
                label="Chỉ cho hạng"
                value={`#${campaign.target_tier_id}`}
              />
            )}
          </div>
        </article>

        <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <h3 className="font-headline text-[15px] font-bold text-slate-800">
            Thể lệ & hướng dẫn
          </h3>
          <div className="mt-3 space-y-3 text-[13px] text-slate-600">
            {campaign.terms ? (
              <TextBlock label="Điều khoản" content={campaign.terms} />
            ) : null}
            {campaign.usage_guide ? (
              <TextBlock
                label="Hướng dẫn sử dụng"
                content={campaign.usage_guide}
              />
            ) : null}
            {campaign.support_contact ? (
              <TextBlock
                label="Liên hệ hỗ trợ"
                content={campaign.support_contact}
              />
            ) : null}
            {!campaign.terms &&
              !campaign.usage_guide &&
              !campaign.support_contact && (
                <p className="text-[12px] italic text-slate-400">
                  Chưa khai báo điều khoản, hướng dẫn sử dụng hay liên hệ hỗ trợ.
                </p>
              )}
          </div>
        </article>
      </section>

      {/* Uỷ quyền */}
      <section className="mt-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-brand-indigo" />
          <h3 className="font-headline text-[15px] font-bold text-slate-800">
            Uỷ quyền
          </h3>
        </div>
        <div className="mt-3">
          {linkedAuth ? (
            <div className="flex items-center justify-between text-[13px]">
              <div className="space-y-1">
                <p className="text-slate-600">
                  Ký lúc:{" "}
                  <span className="font-medium text-slate-800">
                    {new Date(linkedAuth.signed_at).toLocaleString("vi-VN")}
                  </span>
                </p>
                {linkedAuth.revoked_at && (
                  <p className="text-red-600">
                    Đã thu hồi lúc:{" "}
                    {new Date(linkedAuth.revoked_at).toLocaleString("vi-VN")}
                  </p>
                )}
              </div>
              <Link
                href={`/merchant/authorizations/${linkedAuth.id}`}
                className="rounded-xl bg-indigo-50 px-3 py-1.5 text-[12px] font-medium text-brand-indigo hover:bg-indigo-100"
              >
                Xem uỷ quyền
              </Link>
            </div>
          ) : (
            <p className="text-[13px] italic text-slate-400">
              Chưa có uỷ quyền liên kết. Nếu chiến dịch được tạo qua
              managed-service, uỷ quyền sẽ hiện ở đây.
            </p>
          )}
        </div>
      </section>

      {/* Phí dịch vụ */}
      <section className="mt-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <h3 className="font-headline text-[15px] font-bold text-slate-800">
          Phí dịch vụ
        </h3>
        <div className="mt-3">
          {!serviceFees || serviceFees.length === 0 ? (
            <p className="text-[13px] italic text-slate-400">
              Đồ án không áp dụng phí dịch vụ (SERVICE_FEE_ENABLED=false).
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[12px]">
                <thead>
                  <tr className="border-b border-slate-100 text-left text-slate-400">
                    <th className="pb-1 pr-3">Loại phí</th>
                    <th className="pb-1 pr-3">Số tiền</th>
                    <th className="pb-1 pr-3">VAT</th>
                    <th className="pb-1 pr-3">Tổng</th>
                    <th className="pb-1 pr-3">Trạng thái</th>
                    <th className="pb-1 pr-3">Hoá đơn</th>
                    <th className="pb-1">Thanh toán</th>
                  </tr>
                </thead>
                <tbody>
                  {serviceFees.map((f) => (
                    <tr key={f.id} className="border-b border-slate-50">
                      <td className="py-1 pr-3 font-medium text-slate-700">
                        {f.fee_type}
                      </td>
                      <td className="py-1 pr-3 text-slate-700">
                        {f.amount.toLocaleString("vi-VN")}₫
                      </td>
                      <td className="py-1 pr-3 text-slate-700">
                        {f.vat_amount.toLocaleString("vi-VN")}₫
                      </td>
                      <td className="py-1 pr-3 font-bold text-slate-800">
                        {f.total_with_vat.toLocaleString("vi-VN")}₫
                      </td>
                      <td className="py-1 pr-3">
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">
                          {f.status}
                        </span>
                      </td>
                      <td className="py-1 pr-3 text-slate-500">
                        {f.invoiced_at
                          ? new Date(f.invoiced_at).toLocaleDateString("vi-VN")
                          : "—"}
                      </td>
                      <td className="py-1 text-slate-500">
                        {f.paid_at
                          ? new Date(f.paid_at).toLocaleDateString("vi-VN")
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  hint,
  tone,
}: {
  icon: typeof Gift;
  label: string;
  value: string;
  hint?: string;
  tone: "indigo" | "green" | "rose" | "emerald";
}) {
  const toneMap = {
    indigo: "bg-indigo-50 text-brand-indigo",
    green: "bg-emerald-50 text-emerald-600",
    rose: "bg-rose-50 text-rose-600",
    emerald: "bg-teal-50 text-teal-600",
  } as const;
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${toneMap[tone]}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[11px] text-slate-400">{label}</p>
          <p className="font-headline text-[18px] font-bold text-slate-800">
            {value}
          </p>
        </div>
      </div>
      {hint && <p className="mt-2 text-[11px] text-slate-500">{hint}</p>}
    </article>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Gift;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50 text-slate-500">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[11px] text-slate-400">{label}</p>
        <p className="truncate font-medium text-slate-700">{value}</p>
      </div>
    </div>
  );
}

function TextBlock({ label, content }: { label: string; content: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-1 whitespace-pre-line text-[13px] text-slate-700">
        {content}
      </p>
    </div>
  );
}
