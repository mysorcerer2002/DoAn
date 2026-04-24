"use client";

import { Loader2, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { useAuthorizations } from "@/lib/hooks/use-partner-enroll";

function formatDate(iso: string): string {
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

export default function AuthorizationsPage() {
  const { data: authorizations, isLoading, isError } = useAuthorizations();

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-brand-indigo">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <p className="text-[12px] text-slate-400">
            Marketing / Uỷ quyền
          </p>
          <h1 className="mt-0.5 font-headline text-[28px] font-bold text-slate-800">
            Danh sách uỷ quyền
          </h1>
        </div>
      </header>

      <div className="mt-6">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
          </div>
        ) : isError ? (
          <p className="py-8 text-center text-red-600">
            Không tải được danh sách uỷ quyền
          </p>
        ) : !authorizations || authorizations.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-16 text-center">
            <ShieldCheck className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-bold text-slate-700">
              Chưa có uỷ quyền nào
            </p>
            <p className="mt-1 text-[13px] text-slate-500">
              Uỷ quyền được tạo khi bạn đăng ký chiến dịch managed-service.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-sm">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-slate-100 text-left">
                  <th className="px-4 py-3 font-medium text-slate-400">
                    Phạm vi
                  </th>
                  <th className="px-4 py-3 font-medium text-slate-400">
                    Chiến dịch
                  </th>
                  <th className="px-4 py-3 font-medium text-slate-400">
                    Hash tài liệu
                  </th>
                  <th className="px-4 py-3 font-medium text-slate-400">
                    Ký lúc
                  </th>
                  <th className="px-4 py-3 font-medium text-slate-400">
                    Hiệu lực
                  </th>
                  <th className="px-4 py-3 font-medium text-slate-400">
                    Trạng thái
                  </th>
                </tr>
              </thead>
              <tbody>
                {authorizations.map((auth) => (
                  <tr
                    key={auth.id}
                    className="border-b border-slate-50 transition hover:bg-slate-50/60"
                  >
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-brand-indigo">
                        {SCOPE_LABEL[auth.scope] ?? auth.scope}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {auth.campaign_id ? (
                        <Link
                          href={`/partner/campaigns/${auth.campaign_id}`}
                          className="font-medium text-brand-indigo hover:underline"
                        >
                          #{auth.campaign_id}
                        </Link>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                      {auth.document_content_hash.slice(0, 12)}…
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {formatDate(auth.signed_at)}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {new Date(auth.valid_from).toLocaleDateString("vi-VN")}{" "}
                      →{" "}
                      {new Date(auth.valid_until).toLocaleDateString("vi-VN")}
                    </td>
                    <td className="px-4 py-3">
                      {auth.revoked_at ? (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-medium text-red-700">
                          Đã thu hồi
                        </span>
                      ) : (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
                          Hiệu lực
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/partner/authorizations/${auth.id}`}
                        className="text-[12px] text-brand-indigo hover:underline"
                      >
                        Xem chi tiết
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
