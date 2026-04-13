"use client";

import { Search, ShieldAlert, ShieldCheck, Users } from "lucide-react";
import { useState } from "react";

import { useAdminUsers } from "@/lib/hooks/use-merchant";
import type { AdminUserRow } from "@/types/merchant";

function roleBadge(role: string) {
  if (role === "super_admin")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-bold text-red-600">
        <ShieldAlert className="h-3 w-3" />
        Super Admin
      </span>
    );
  if (role === "admin")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-bold text-brand-indigo">
        <ShieldCheck className="h-3 w-3" />
        Admin
      </span>
    );
  return (
    <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-600">
      Người dùng
    </span>
  );
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<"regular" | "admin" | "super_admin" | "">("");
  const { data, isLoading } = useAdminUsers({
    q: search.trim() || undefined,
    role: role || undefined,
    limit: 100,
  });

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <p className="text-[12px] text-slate-400">Hệ thống / Người dùng</p>
          <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
            Người dùng platform
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            Tổng {data?.total ?? 0} tài khoản
          </p>
        </div>
      </header>

      <section className="mt-6 flex flex-col gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo email, tên hoặc số điện thoại"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
          />
        </div>
        <div className="flex gap-2">
          {(["", "regular", "admin", "super_admin"] as const).map((r) => (
            <button
              key={r || "all"}
              type="button"
              onClick={() => setRole(r)}
              className={
                role === r
                  ? "rounded-lg bg-brand-indigo px-4 py-2 text-[12px] font-bold text-white"
                  : "rounded-lg border border-slate-200 bg-white px-4 py-2 text-[12px] font-medium text-slate-600 hover:bg-slate-50"
              }
            >
              {r === "" ? "Tất cả" : r === "super_admin" ? "Super Admin" : r === "admin" ? "Admin" : "User"}
            </button>
          ))}
        </div>
      </section>

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex min-h-[30vh] items-center justify-center text-slate-400">
            Đang tải danh sách...
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-8 py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-brand-indigo">
              <Users className="h-8 w-8" />
            </div>
            <p className="mt-4 font-headline text-[16px] font-bold text-slate-700">
              Không có người dùng nào
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-[13px]">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-6 py-3">Người dùng</th>
                <th className="px-6 py-3">Liên hệ</th>
                <th className="px-6 py-3">Vai trò</th>
                <th className="px-6 py-3">Trạng thái</th>
                <th className="px-6 py-3">Đăng ký</th>
                <th className="px-6 py-3">Lần cuối</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((u: AdminUserRow) => (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 font-bold text-brand-indigo">
                        {(u.full_name || u.email || "?")[0]?.toUpperCase()}
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">
                          {u.full_name || "—"}
                        </p>
                        <p className="text-[11px] text-slate-400">#{u.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-600">
                    <p>{u.email || "—"}</p>
                    {u.phone && (
                      <p className="text-[11px] text-slate-400">{u.phone}</p>
                    )}
                  </td>
                  <td className="px-6 py-4">{roleBadge(u.system_role)}</td>
                  <td className="px-6 py-4">
                    {u.is_active ? (
                      <span className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-[11px] font-medium text-green-700">
                        Hoạt động
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
                        Khoá
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {fmtDate(u.created_at)}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {fmtDate(u.last_login_at)}
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
