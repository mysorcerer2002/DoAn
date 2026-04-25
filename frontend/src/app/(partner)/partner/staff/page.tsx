"use client";

import {
  Crown,
  Loader2,
  Mail,
  Plus,
  Trash2,
  Users,
  UsersRound,
  X,
} from "lucide-react";
import { useState } from "react";

import {
  useAddStaff,
  useRemoveStaff,
  useStaff,
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

export default function MerchantStaffPage() {
  const { data: staffList, isLoading, isError } = useStaff();
  const addMutation = useAddStaff();
  const removeMutation = useRemoveStaff();

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    role: "staff" as "owner" | "staff",
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.email.trim()) {
      setError("Vui lòng nhập email");
      return;
    }
    try {
      await addMutation.mutateAsync({
        email: form.email.trim(),
        full_name: form.full_name.trim() || null,
        role: form.role,
      });
      setForm({ email: "", full_name: "", role: "staff" });
      setModalOpen(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? "Lỗi thêm nhân viên");
    }
  };

  const handleRemove = async (id: number) => {
    if (!confirm("Xác nhận xoá nhân viên này?")) return;
    try {
      await removeMutation.mutateAsync(id);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail ?? "Không xoá được nhân viên");
    }
  };

  const owners = staffList?.filter((s) => s.role === "owner").length ?? 0;
  const staff = staffList?.filter((s) => s.role === "staff").length ?? 0;

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:justify-between">
        <div>
          <h1 className="font-headline text-[32px] font-bold text-slate-800">
            Quản lý nhân viên
          </h1>
          <p className="mt-1 text-[14px] text-slate-500">
            {staffList?.length ?? 0} nhân viên ({owners} chủ / {staff} nhân viên)
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet px-5 py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          Mời nhân viên
        </button>
      </header>

      {isLoading ? (
        <div className="mt-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
        </div>
      ) : isError ? (
        <div className="mt-10 text-center text-red-600">
          Không tải được danh sách nhân viên
        </div>
      ) : staffList?.length === 0 ? (
        <div className="mt-10 rounded-2xl border border-dashed border-slate-200 bg-white p-16 text-center">
          <UsersRound className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-4 font-bold text-slate-700">Chưa có nhân viên</p>
        </div>
      ) : (
        <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {staffList?.map((s: StaffResponse) => (
            <article
              key={s.id}
              className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-col items-center text-center">
                <div
                  className={
                    s.role === "owner"
                      ? "flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-2xl font-bold text-white"
                      : "flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-brand-indigo to-brand-violet text-2xl font-bold text-white"
                  }
                >
                  {getInitials(s.user_full_name, s.user_email)}
                </div>
                <h3 className="mt-3 font-headline text-[15px] font-bold text-slate-800">
                  {s.user_full_name ?? "Chưa đặt tên"}
                </h3>
                <span
                  className={
                    s.role === "owner"
                      ? "mt-2 inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-0.5 text-[11px] font-bold text-white"
                      : "mt-2 inline-flex items-center rounded-full bg-indigo-50 px-3 py-0.5 text-[11px] font-bold text-brand-indigo"
                  }
                >
                  {s.role === "owner" && (
                    <Crown className="h-2.5 w-2.5" fill="white" />
                  )}
                  {s.role === "owner" ? "Chủ cửa hàng" : "Nhân viên"}
                </span>
                {s.user_email && (
                  <p className="mt-1.5 flex items-center gap-1 text-[10px] text-slate-400">
                    <Mail className="h-3 w-3" />
                    {s.user_email}
                  </p>
                )}
                {s.role !== "owner" && (
                  <button
                    type="button"
                    onClick={() => handleRemove(s.id)}
                    className="mt-4 flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-[12px] font-bold text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-3 w-3" />
                    Xoá
                  </button>
                )}
              </div>
            </article>
          ))}
        </section>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-md space-y-4 rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-[20px] font-bold text-slate-800">
                Mời nhân viên mới
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
                aria-label="Đóng"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
                <div>
                  <label className="text-[12px] font-medium text-slate-500">
                    Email
                  </label>
                  <input
                    required
                    type="email"
                    value={form.email}
                    onChange={(e) =>
                      setForm({ ...form, email: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                  />
                </div>
                <div>
                  <label className="text-[12px] font-medium text-slate-500">
                    Họ tên
                  </label>
                  <input
                    type="text"
                    value={form.full_name}
                    onChange={(e) =>
                      setForm({ ...form, full_name: e.target.value })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
                  />
                </div>
                <div>
                  <label className="text-[12px] font-medium text-slate-500">
                    Vai trò
                  </label>
                  <select
                    value={form.role}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        role: e.target.value as "owner" | "staff",
                      })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo"
                  >
                    <option value="staff">Nhân viên</option>
                    <option value="owner">Chủ cửa hàng</option>
                  </select>
                </div>

                {error && (
                  <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">
                    {error}
                  </div>
                )}

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
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
                    Gửi lời mời
                  </button>
                </div>
              </form>
          </div>
        </div>
      )}
    </main>
  );
}
