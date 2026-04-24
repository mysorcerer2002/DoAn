"use client";

import {
  ArrowLeft,
  Copy,
  Loader2,
  ShieldCheck,
  ShieldOff,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import {
  useAuthorizationDetail,
  useRevokeAuthorization,
} from "@/lib/hooks/use-partner-enroll";

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const SCOPE_LABEL: Record<string, string> = {
  per_campaign: "Theo chiến dịch",
  global: "Toàn cục",
};

const METHOD_LABEL: Record<string, string> = {
  click_to_sign: "Click to Sign",
};

export default function AuthorizationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);

  const { data: auth, isLoading, isError } = useAuthorizationDetail(
    Number.isFinite(id) ? id : null,
  );
  const revokeMutation = useRevokeAuthorization();

  const [revokeModalOpen, setRevokeModalOpen] = useState(false);
  const [revokeReason, setRevokeReason] = useState("");
  const [revokeError, setRevokeError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleRevoke() {
    setRevokeError(null);
    try {
      await revokeMutation.mutateAsync({
        id,
        reason: revokeReason.trim() || undefined,
      });
      setRevokeModalOpen(false);
    } catch (e: unknown) {
      const err = e as {
        response?: {
          data?: {
            detail?:
              | string
              | { code?: string; message?: string };
          };
        };
      };
      const detail = err.response?.data?.detail;
      if (
        typeof detail === "object" &&
        detail?.code === "REVOKE_BLOCKED_OPS_STARTED"
      ) {
        setRevokeError(
          "Ops đã bắt đầu nộp Sở CT — không thể thu hồi uỷ quyền này.",
        );
      } else if (typeof detail === "string") {
        setRevokeError(detail);
      } else {
        setRevokeError("Lỗi thu hồi uỷ quyền");
      }
    }
  }

  function handleCopyHash() {
    if (!auth) return;
    navigator.clipboard.writeText(auth.document_content_hash).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  if (isLoading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  if (isError || !auth) {
    return (
      <main className="px-4 py-8 md:px-8">
        <Link
          href="/merchant/authorizations"
          className="inline-flex items-center gap-1 text-[13px] text-brand-indigo"
        >
          <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
        </Link>
        <p className="mt-6 text-center text-red-600">
          Không tìm thấy uỷ quyền.
        </p>
      </main>
    );
  }

  const isRevoked = !!auth.revoked_at;
  const sp = auth.signature_payload;

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <Link
        href="/merchant/authorizations"
        className="inline-flex items-center gap-1 text-[12px] text-slate-500 hover:text-brand-indigo"
      >
        <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
      </Link>

      <header className="mt-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Marketing / Uỷ quyền</p>
          <h1 className="mt-0.5 font-headline text-[26px] font-bold text-slate-800">
            Uỷ quyền #{auth.id}
          </h1>
        </div>
        {!isRevoked && (
          <button
            type="button"
            onClick={() => setRevokeModalOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-[13px] font-medium text-red-700 hover:bg-red-100"
          >
            <ShieldOff className="h-4 w-4" />
            Thu hồi uỷ quyền
          </button>
        )}
      </header>

      {/* Revoked banner */}
      {isRevoked && (
        <div className="mt-4 rounded-xl bg-red-50 px-5 py-4 border border-red-200">
          <div className="flex items-center gap-2">
            <ShieldOff className="h-5 w-5 text-red-600" />
            <p className="font-bold text-red-700">Uỷ quyền đã bị thu hồi</p>
          </div>
          <p className="mt-1 text-[12px] text-red-600">
            Thu hồi lúc: {formatDate(auth.revoked_at)}
          </p>
          {auth.revoked_reason && (
            <p className="mt-1 text-[12px] text-red-600">
              Lý do: {auth.revoked_reason}
            </p>
          )}
        </div>
      )}

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {/* Thông tin chung */}
        <section className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand-indigo" />
            <h2 className="font-headline text-[14px] font-bold text-slate-800">
              Thông tin chung
            </h2>
          </div>
          <dl className="mt-3 space-y-2 text-[13px]">
            <InfoRow label="Phạm vi">
              <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-brand-indigo">
                {SCOPE_LABEL[auth.scope] ?? auth.scope}
              </span>
            </InfoRow>
            <InfoRow label="Chiến dịch">
              {auth.campaign_id ? (
                <Link
                  href={`/merchant/campaigns/${auth.campaign_id}`}
                  className="font-medium text-brand-indigo hover:underline"
                >
                  #{auth.campaign_id}
                </Link>
              ) : (
                "—"
              )}
            </InfoRow>
            <InfoRow label="Ký lúc">{formatDate(auth.signed_at)}</InfoRow>
            <InfoRow label="Phương thức ký">
              {METHOD_LABEL[auth.signature_method] ?? auth.signature_method}
            </InfoRow>
            <InfoRow label="Hiệu lực từ">
              {formatDate(auth.valid_from)}
            </InfoRow>
            <InfoRow label="Hiệu lực đến">
              {formatDate(auth.valid_until)}
            </InfoRow>
          </dl>
        </section>

        {/* Metadata chữ ký */}
        <section className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <h2 className="font-headline text-[14px] font-bold text-slate-800">
            Metadata chữ ký
          </h2>
          <dl className="mt-3 space-y-2 text-[13px]">
            {sp.ip && <InfoRow label="IP">{sp.ip}</InfoRow>}
            {sp.user_agent && (
              <InfoRow label="User Agent">
                <span className="break-all text-[11px]">{sp.user_agent}</span>
              </InfoRow>
            )}
            {sp.otp_purpose && (
              <InfoRow label="Mục đích OTP">{sp.otp_purpose}</InfoRow>
            )}
            {sp.consent_text_version && (
              <InfoRow label="Phiên bản điều khoản">
                <span className="font-mono">{sp.consent_text_version}</span>
              </InfoRow>
            )}
            {sp.template_version != null && (
              <InfoRow label="Phiên bản template">
                v{sp.template_version}
              </InfoRow>
            )}
            {sp.otp_attempts_count != null && (
              <InfoRow label="Số lần thử OTP">
                {sp.otp_attempts_count}
              </InfoRow>
            )}
            {sp.signed_at_server && (
              <InfoRow label="Thời gian server">
                {formatDate(sp.signed_at_server)}
              </InfoRow>
            )}
            {sp.rendered_pdf_hash && (
              <InfoRow label="PDF hash">
                <span className="break-all font-mono text-[11px]">
                  {sp.rendered_pdf_hash.slice(0, 20)}…
                </span>
              </InfoRow>
            )}
            {!sp.ip &&
              !sp.user_agent &&
              !sp.otp_purpose &&
              !sp.consent_text_version &&
              sp.template_version == null &&
              sp.otp_attempts_count == null && (
                <p className="text-[12px] italic text-slate-400">
                  Không có metadata.
                </p>
              )}
          </dl>
        </section>
      </div>

      {/* Hash tài liệu */}
      <section className="mt-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-[14px] font-bold text-slate-800">
            Hash tài liệu
          </h2>
          <button
            type="button"
            onClick={handleCopyHash}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-[12px] font-medium text-slate-600 hover:bg-slate-50"
          >
            <Copy className="h-3.5 w-3.5" />
            {copied ? "Đã sao chép!" : "Sao chép"}
          </button>
        </div>
        <p className="mt-2 break-all rounded-xl bg-slate-50 p-3 font-mono text-[12px] text-slate-700">
          {auth.document_content_hash}
        </p>
      </section>

      {/* Revoke modal */}
      {revokeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-md space-y-4 rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="font-headline text-[18px] font-bold text-slate-800">
              Thu hồi uỷ quyền
            </h2>
            <p className="text-[13px] text-slate-600">
              Hành động này không thể hoàn tác. Nhập lý do thu hồi (tuỳ chọn):
            </p>
            <textarea
              rows={3}
              value={revokeReason}
              onChange={(e) => setRevokeReason(e.target.value)}
              placeholder="Lý do thu hồi..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
            />
            {revokeError && (
              <div className="rounded-xl bg-red-50 px-4 py-3 text-[13px] text-red-700">
                {revokeError}
              </div>
            )}
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setRevokeModalOpen(false);
                  setRevokeError(null);
                }}
                className="rounded-xl border border-slate-200 px-4 py-2 text-[13px] font-medium text-slate-700 hover:bg-slate-50"
              >
                Huỷ
              </button>
              <button
                type="button"
                onClick={handleRevoke}
                disabled={revokeMutation.isPending}
                className="rounded-xl bg-red-600 px-4 py-2 text-[13px] font-bold text-white hover:bg-red-700 disabled:opacity-60"
              >
                {revokeMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Xác nhận thu hồi"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function InfoRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="shrink-0 text-slate-400">{label}</dt>
      <dd className="text-right font-medium text-slate-700">{children}</dd>
    </div>
  );
}
