"use client";

import {
  Clock,
  Database,
  Globe,
  KeyRound,
  Settings,
  ShieldCheck,
  Timer,
} from "lucide-react";

import { useAdminSettings } from "@/lib/hooks/use-partner";

export default function AdminSettingsPage() {
  const { data, isLoading } = useAdminSettings();

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Hệ thống / Cài đặt</p>
        <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
          Cài đặt hệ thống
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Cấu hình platform đang chạy. Chỉ đọc — thay đổi qua biến môi trường.
        </p>
      </header>

      {isLoading || !data ? (
        <div className="mt-8 rounded-2xl border border-slate-100 bg-white p-12 text-center text-slate-400 shadow-sm">
          Đang tải cấu hình...
        </div>
      ) : (
        <>
          <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
            <SectionCard
              icon={Settings}
              title="Ứng dụng"
              color="indigo"
              rows={[
                { label: "Tên ứng dụng", value: data.app_name },
                {
                  label: "Môi trường",
                  value: (
                    <span
                      className={
                        data.environment === "production"
                          ? "inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-[11px] font-bold text-green-700"
                          : "inline-flex items-center rounded-full bg-orange-50 px-2.5 py-0.5 text-[11px] font-bold text-brand-orange"
                      }
                    >
                      {data.environment}
                    </span>
                  ),
                },
                {
                  label: "Debug mode",
                  value: data.debug ? "Bật" : "Tắt",
                },
              ]}
            />

            <SectionCard
              icon={KeyRound}
              title="Xác thực JWT"
              color="violet"
              rows={[
                {
                  label: "Access token TTL",
                  value: `${data.jwt_expire_minutes} phút`,
                },
                {
                  label: "Refresh token TTL",
                  value: `${data.refresh_expire_days} ngày`,
                },
                { label: "Thuật toán", value: "HS256" },
              ]}
            />

            <SectionCard
              icon={Timer}
              title="Scheduler"
              color="orange"
              rows={[
                {
                  label: "Trạng thái",
                  value: data.scheduler_enabled ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-[11px] font-bold text-green-700">
                      <Clock className="h-3 w-3" />
                      Đang chạy
                    </span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
                      Tắt
                    </span>
                  ),
                },
                {
                  label: "Jobs đã cấu hình",
                  value: "Birthday voucher (VN timezone)",
                },
              ]}
            />

            <SectionCard
              icon={ShieldCheck}
              title="Bảo mật"
              color="green"
              rows={[
                { label: "HTTPS enforce", value: "Qua Cloudflare Tunnel" },
                { label: "Rate limit /login", value: "10/minute" },
                { label: "Rate limit /register", value: "5/minute" },
                { label: "Password min length", value: "8 ký tự" },
              ]}
            />
          </section>

          <section className="mt-6 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-brand-indigo">
                <Globe className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <h3 className="font-headline text-[16px] font-bold text-slate-800">
                  CORS Origins
                </h3>
                <p className="mt-1 text-[12px] text-slate-500">
                  Frontend origins được phép gọi API
                </p>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {data.allowed_origins.map((origin) => (
                    <li
                      key={origin}
                      className="rounded-lg bg-slate-50 px-3 py-1.5 font-mono text-[11px] text-slate-700"
                    >
                      {origin}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="mt-6 rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-violet-50 p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-brand-indigo shadow-sm">
                <Database className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-headline text-[16px] font-bold text-slate-800">
                  Cơ sở dữ liệu
                </h3>
                <p className="mt-1 text-[12px] text-slate-600">
                  PostgreSQL 15 — multi-partner column-based isolation via
                  X-Partner-Id header. Migrations Alembic chạy tự động khi
                  container khởi động.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

const COLOR_MAP: Record<string, string> = {
  indigo: "bg-indigo-50 text-brand-indigo",
  violet: "bg-violet-50 text-brand-violet",
  orange: "bg-orange-50 text-brand-orange",
  green: "bg-green-50 text-green-600",
};

function SectionCard({
  icon: Icon,
  title,
  color,
  rows,
}: {
  icon: typeof Settings;
  title: string;
  color: string;
  rows: { label: string; value: React.ReactNode }[];
}) {
  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${COLOR_MAP[color] ?? COLOR_MAP.indigo}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="font-headline text-[15px] font-bold text-slate-800">
          {title}
        </h3>
      </div>
      <dl className="divide-y divide-slate-100">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between py-3 text-[13px]"
          >
            <dt className="text-slate-500">{row.label}</dt>
            <dd className="font-medium text-slate-800">{row.value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
