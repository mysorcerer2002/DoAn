"use client";

import {
  Eye,
  EyeOff,
  Loader2,
  Mail,
  Phone,
  Plus,
  Power,
  RotateCcw,
  UsersRound,
  X,
} from "lucide-react";
import { useState } from "react";

import {
  useAddStaff,
  useResetStaffPassword,
  useStaff,
  useToggleStaffActive,
} from "@/lib/hooks/use-partner";
import type { StaffResponse } from "@/types/partner";

function getInitials(name: string | null, email: string | null): string {
  const source = name ?? email ?? "?";
  const parts = source.trim().split(/\s+/);
  return parts
    .slice(-2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

const FILTER_OPTIONS = [
  { value: "all", label: "Tất cả" },
  { value: "true", label: "Đang hoạt động" },
  { value: "false", label: "Đã vô hiệu" },
] as const;

type ActiveFilter = "all" | "true" | "false";

export default function MerchantStaffPage() {
  const [filter, setFilter] = useState<ActiveFilter>("all");
  const { data, isLoading, isError } = useStaff({ is_active: filter });
  const addMutation = useAddStaff();
  const toggleMutation = useToggleStaffActive();
  const resetMutation = useResetStaffPassword();

  // Add-staff dialog
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({
    email: "",
    phone: "",
    full_name: "",
    password: "",
  });
  const [addError, setAddError] = useState<string | null>(null);

  // Reset-password result dialog
  const [resetResult, setResetResult] = useState<{
    name: string | null;
    temp_password: string;
    email_sent: boolean;
  } | null>(null);
  const [showPwd, setShowPwd] = useState(false);

  const staffList = data?.items ?? [];
  const total = data?.total ?? 0;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError(null);
    if (!form.full_name.trim()) {
      setAddError("Vui lòng nhập họ tên");
      return;
    }
    if (!form.email.trim() && !form.phone.trim()) {
      setAddError("Cần ít nhất email hoặc số điện thoại");
      return;
    }
    if (form.password.length < 8) {
      setAddError("Mật khẩu tối thiểu 8 ký tự");
      return;
    }
    try {
      await addMutation.mutateAsync({
        email: form.email.trim() || undefined,
        phone: form.phone.trim() || undefined,
        full_name: form.full_name.trim(),
        password: form.password,
      });
      setForm({ email: "", phone: "", full_name: "", password: "" });
      setAddOpen(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setAddError(err.response?.data?.detail ?? "Lỗi thêm nhân viên");
    }
  };

  const handleToggle = async (s: StaffResponse) => {
    const action = s.is_active ? "vô hiệu hoá" : "kích hoạt";
    if (!confirm(`Xác nhận ${action} nhân viên ${s.full_name ?? s.email ?? s.user_id}?`))
      return;
    try {
      await toggleMutation.mutateAsync({ user_id: s.user_id, is_active: !s.is_active });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail ?? "Không cập nhật được trạng thái");
    }
  };

  const handleReset = async (s: StaffResponse) => {
    if (!confirm(`Reset mật khẩu cho ${s.full_name ?? s.email ?? s.user_id}?`)) return;
    try {
      const res = await resetMutation.mutateAsync(s.user_id);
      setResetResult({
        name: s.full_name,
        temp_password: res.temp_password,
        email_sent: res.email_sent,
      });
      setShowPwd(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail ?? "Không reset được mật khẩu");
    }
  };

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="font-headline text-[32px] font-bold text-slate-800">
            Quản lý nhân viên
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">{total} nhân viên</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as ActiveFilter)}
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
          >
            {FILTER_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setAddOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            Thêm nhân viên
          </button>
        </div>
      </header>

      {isLoading ? (
        <div className="mt-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
        </div>
      ) : isError ? (
        <div className="mt-10 text-center text-red-600">
          Không tải được danh sách nhân viên
        </div>
      ) : staffList.length === 0 ? (
        <div className="mt-10 rounded-2xl border border-dashed border-slate-200 bg-white p-16 text-center">
          <UsersRound className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-4 font-bold text-slate-700">Chưa có nhân viên</p>
        </div>
      ) : (
        <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {staffList.map((s: StaffResponse) => (
            <article
              key={s.id}
              className={`rounded-2xl border bg-white p-5 shadow-sm ${
                s.is_active ? "border-slate-100" : "border-slate-200 opacity-60"
              }`}
            >
              <div className="flex flex-col items-center text-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-brand-indigo to-brand-violet text-2xl font-bold text-white">
                  {getInitials(s.full_name, s.email)}
                </div>
                <h3 className="mt-3 font-headline text-[15px] font-bold text-slate-800">
                  {s.full_name ?? "Chưa đặt tên"}
                </h3>
                <span
                  className={`mt-2 inline-flex items-center rounded-full px-3 py-0.5 text-[11px] font-bold ${
                    s.is_active
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {s.is_active ? "Hoạt động" : "Vô hiệu"}
                </span>
                {s.email && (
                  <p className="mt-1.5 flex items-center gap-1 text-[10px] text-slate-400">
                    <Mail className="h-3 w-3" />
                    {s.email}
                  </p>
                )}
                {s.phone && (
                  <p className="mt-0.5 flex items-center gap-1 text-[10px] text-slate-400">
                    <Phone className="h-3 w-3" />
                    {s.phone}
                  </p>
                )}
                <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleToggle(s)}
                    disabled={toggleMutation.isPending}
                    className={`flex items-center gap-1 rounded-lg border px-3 py-1.5 text-[12px] font-bold ${
                      s.is_active
                        ? "border-orange-200 text-orange-600 hover:bg-orange-50"
                        : "border-emerald-200 text-emerald-600 hover:bg-emerald-50"
                    }`}
                  >
                    <Power className="h-3 w-3" />
                    {s.is_active ? "Vô hiệu" : "Kích hoạt"}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleReset(s)}
                    disabled={resetMutation.isPending}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-[12px] font-bold text-slate-600 hover:bg-slate-50"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Reset
                  </button>
                </div>
              </div>
            </article>
          ))}
        </section>
      )}

      {/* Add staff dialog */}
      {addOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-md space-y-4 rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-[20px] font-bold text-slate-800">
                Thêm nhân viên mới
              </h2>
              <button
                type="button"
                onClick={() => setAddOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
                aria-label="Đóng"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAdd} className="space-y-3">
              <div>
                <label className="text-[12px] font-medium text-slate-500">
                  Họ tên <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  type="text"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
                Cần ít nhất 1 trong 2 trường <strong>Email</strong> hoặc{" "}
                <strong>Số điện thoại</strong> để nhân viên đăng nhập được.
              </div>
              <div>
                <label className="text-[12px] font-medium text-slate-500">
                  Email
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>
              <div>
                <label className="text-[12px] font-medium text-slate-500">
                  Số điện thoại
                </label>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>
              <div>
                <label className="text-[12px] font-medium text-slate-500">
                  Mật khẩu <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="Tối thiểu 8 ký tự"
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                />
              </div>

              {addError && (
                <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">
                  {addError}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAddOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-[13px] font-medium text-slate-700 hover:bg-slate-50"
                >
                  Huỷ
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending}
                  className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
                >
                  {addMutation.isPending && (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  )}
                  Thêm nhân viên
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset password result dialog */}
      {resetResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-[18px] font-bold text-slate-800">
                Mật khẩu tạm thời
              </h2>
              <button
                type="button"
                onClick={() => setResetResult(null)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
                aria-label="Đóng"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-[13px] text-slate-500">
              {resetResult.name && (
                <>
                  Mật khẩu mới cho <strong>{resetResult.name}</strong>:
                </>
              )}
            </p>
            <div className="flex items-center gap-2 rounded-xl bg-slate-100 px-4 py-3">
              <code className="flex-1 text-[15px] font-bold tracking-wider text-slate-800">
                {showPwd ? resetResult.temp_password : "••••••••••••"}
              </code>
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                className="text-slate-400 hover:text-slate-700"
              >
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {resetResult.email_sent ? (
              <p className="text-[12px] text-emerald-600">
                Email thông báo đã được gửi tới nhân viên.
              </p>
            ) : (
              <p className="text-[12px] text-amber-600">
                Không gửi được email — hãy cung cấp mật khẩu trực tiếp cho nhân viên.
              </p>
            )}
            <button
              type="button"
              onClick={() => setResetResult(null)}
              className="w-full rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-2.5 text-[13px] font-bold text-white"
            >
              Đã xong
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
