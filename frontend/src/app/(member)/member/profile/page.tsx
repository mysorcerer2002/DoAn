"use client";

import {
  ArrowLeft,
  Calendar,
  ChevronRight,
  Crown,
  Loader2,
  LogOut,
  Mail,
  Pencil,
  Phone,
  ScrollText,
  Settings,
  Shield,
  User as UserIcon,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { authApi } from "@/lib/api";
import { useLogout } from "@/lib/hooks/use-logout";
import { useMe, useMyMemberships } from "@/lib/hooks/use-me";
import type { User } from "@/types/auth";

function getInitials(fullName: string | null): string {
  if (!fullName) return "M";
  const parts = fullName.trim().split(/\s+/);
  return parts
    .slice(-2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function ProfilePage() {
  const router = useRouter();
  const qc = useQueryClient();
  const { data: user, isLoading, isError } = useMe();
  const { data: memberships } = useMyMemberships();
  const [editOpen, setEditOpen] = useState(false);
  const logout = useLogout();

  const updateMut = useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      setEditOpen(false);
    },
  });

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </div>
    );
  }

  if (isError || !user) {
    router.replace("/login");
    return null;
  }

  const totalPoints =
    memberships?.reduce((sum, m) => sum + m.points_balance, 0) ?? 0;
  const topTier = (memberships ?? [])
    .slice()
    .sort((a, b) => b.points_balance - a.points_balance)[0];

  const handleLogout = () => {
    logout();
  };

  const infoItems = [
    {
      id: "phone",
      icon: Phone,
      label: "Số điện thoại",
      value: user.phone ?? "Chưa cập nhật",
      editable: true,
    },
    {
      id: "email",
      icon: Mail,
      label: "Email",
      value: user.email ?? "Chưa cập nhật",
      editable: false,
    },
    {
      id: "birthday",
      icon: Calendar,
      label: "Ngày sinh",
      value: formatDate(user.birthday),
      editable: true,
    },
    {
      id: "joined",
      icon: Calendar,
      label: "Thành viên từ",
      value: formatDate(user.created_at),
      editable: false,
    },
  ];

  return (
    <>
      <header className="relative h-[260px] overflow-hidden bg-gradient-to-br from-brand-indigo to-brand-violet px-4 pt-4">
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-10 -left-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />

        <div className="relative z-10 flex items-center justify-between">
          <Link
            href="/member"
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-transform hover:bg-white/10 active:scale-95"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <h1 className="font-headline text-[18px] font-bold text-white">
            Tài khoản
          </h1>
          <button
            type="button"
            onClick={() => setEditOpen(true)}
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-transform hover:bg-white/10 active:scale-95"
            aria-label="Chỉnh sửa thông tin"
          >
            <Settings className="h-6 w-6" />
          </button>
        </div>

        <div className="relative z-10 mt-3 flex flex-col items-center">
          <div className="flex h-24 w-24 items-center justify-center rounded-full border-4 border-white bg-gradient-to-br from-indigo-200 to-violet-200 text-2xl font-bold text-indigo-700 shadow-lg">
            {getInitials(user.full_name)}
          </div>
          <h2 className="mt-3 font-headline text-[24px] font-bold text-white">
            {user.full_name ?? "Thành viên"}
          </h2>
          {topTier && (
            <div className="mt-1 flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
              <Crown className="h-3.5 w-3.5 text-white" fill="white" />
              <span className="font-headline text-[12px] font-bold text-white">
                {topTier.current_tier_name ?? "Thành viên mới"}
              </span>
            </div>
          )}
        </div>
      </header>

      <main className="-mt-8 space-y-5 px-4">
        <section className="grid grid-cols-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-lg">
          <Stat
            value={totalPoints.toLocaleString("vi-VN")}
            label="Điểm hiện có"
            tone="orange"
          />
          <Stat
            value={(memberships?.length ?? 0).toString()}
            label="Cửa hàng"
            tone="indigo"
            border
          />
          <Stat value="—" label="Voucher" tone="indigo" />
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <h3 className="font-headline text-[16px] font-bold text-slate-800">
              Thông tin cá nhân
            </h3>
            <button
              type="button"
              onClick={() => setEditOpen(true)}
              className="flex items-center gap-1 text-[12px] font-bold text-brand-indigo hover:underline"
            >
              <Pencil className="h-3.5 w-3.5" />
              Chỉnh sửa
            </button>
          </div>
          <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
            {infoItems.map((item, idx) => (
              <button
                key={item.id}
                type="button"
                onClick={() => item.editable && setEditOpen(true)}
                className={`flex w-full items-center gap-3 px-4 py-3.5 text-left ${
                  idx > 0 ? "border-t border-slate-100" : ""
                } ${item.editable ? "hover:bg-slate-50" : "cursor-default"}`}
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
                  <item.icon className="h-5 w-5 text-brand-indigo" />
                </div>
                <div className="flex-1">
                  <p className="text-[11px] text-slate-400">{item.label}</p>
                  <p className="text-[14px] font-medium text-slate-800">
                    {item.value}
                  </p>
                </div>
                {item.editable && (
                  <ChevronRight className="h-5 w-5 text-slate-300" />
                )}
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h3 className="px-1 font-headline text-[16px] font-bold text-slate-800">
            Khác
          </h3>
          <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
            <div className="flex items-center gap-3 px-4 py-3.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
                <ScrollText className="h-5 w-5 text-brand-indigo" />
              </div>
              <p className="flex-1 text-[14px] font-medium text-slate-800">
                Điều khoản sử dụng
              </p>
              <ChevronRight className="h-5 w-5 text-slate-300" />
            </div>
            <div className="flex items-center gap-3 border-t border-slate-100 px-4 py-3.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
                <Shield className="h-5 w-5 text-brand-indigo" />
              </div>
              <p className="flex-1 text-[14px] font-medium text-slate-800">
                Chính sách bảo mật
              </p>
              <ChevronRight className="h-5 w-5 text-slate-300" />
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center gap-3 border-t border-slate-100 px-4 py-3.5 text-left transition-colors hover:bg-red-50"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50">
                <LogOut className="h-5 w-5 text-red-500" />
              </div>
              <p className="flex-1 text-[14px] font-medium text-red-500">
                Đăng xuất
              </p>
            </button>
          </div>
        </section>
      </main>

      {editOpen && (
        <EditProfileModal
          user={user}
          onClose={() => setEditOpen(false)}
          onSubmit={(data) => updateMut.mutate(data)}
          submitting={updateMut.isPending}
          error={
            updateMut.isError
              ? "Không cập nhật được. Vui lòng kiểm tra dữ liệu."
              : null
          }
        />
      )}
    </>
  );
}

function EditProfileModal({
  user,
  onClose,
  onSubmit,
  submitting,
  error,
}: {
  user: User;
  onClose: () => void;
  onSubmit: (data: {
    full_name?: string;
    phone?: string;
    birthday?: string;
  }) => void;
  submitting: boolean;
  error: string | null;
}) {
  const [fullName, setFullName] = useState(user.full_name ?? "");
  const [phone, setPhone] = useState(user.phone ?? "");
  const [birthday, setBirthday] = useState(user.birthday ?? "");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      full_name: fullName.trim() || undefined,
      phone: phone.trim() || undefined,
      birthday: birthday || undefined,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/60 backdrop-blur-sm sm:items-center"
      onClick={onClose}
    >
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-t-3xl bg-white p-6 shadow-2xl sm:rounded-3xl"
      >
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-[18px] font-bold text-slate-800">
            Chỉnh sửa thông tin
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100"
            aria-label="Đóng"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-5 space-y-4">
          <div className="space-y-1">
            <label
              htmlFor="full_name"
              className="block pl-1 text-[12px] font-medium text-slate-500"
            >
              Họ và tên
            </label>
            <div className="relative">
              <UserIcon className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
              <input
                id="full_name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
                placeholder="Nguyễn Văn A"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label
              htmlFor="phone"
              className="block pl-1 text-[12px] font-medium text-slate-500"
            >
              Số điện thoại
            </label>
            <div className="relative">
              <Phone className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
                placeholder="0901234567"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label
              htmlFor="birthday"
              className="block pl-1 text-[12px] font-medium text-slate-500"
            >
              Ngày sinh
            </label>
            <div className="relative">
              <Calendar className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
              <input
                id="birthday"
                type="date"
                value={birthday}
                onChange={(e) => setBirthday(e.target.value)}
                className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
              />
            </div>
            <p className="pl-1 text-[11px] text-slate-400">
              Dùng để nhận voucher sinh nhật hàng năm
            </p>
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-[12px] text-red-600">
              {error}
            </div>
          )}
        </div>

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-xl border border-slate-200 bg-white py-3 font-headline text-[14px] font-bold text-slate-600 hover:bg-slate-50"
          >
            Huỷ
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="flex-1 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3 font-headline text-[14px] font-bold text-white shadow-lg active:scale-[0.98] disabled:opacity-60"
          >
            {submitting ? "Đang lưu..." : "Lưu thay đổi"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Stat({
  value,
  label,
  tone,
  border,
}: {
  value: string;
  label: string;
  tone: "orange" | "indigo";
  border?: boolean;
}) {
  return (
    <div
      className={
        border
          ? "flex flex-col items-center border-x border-slate-100"
          : "flex flex-col items-center"
      }
    >
      <span
        className={
          tone === "orange"
            ? "font-headline text-[24px] font-bold text-brand-orange"
            : "font-headline text-[24px] font-bold text-brand-indigo"
        }
      >
        {value}
      </span>
      <span className="text-[11px] text-slate-400">{label}</span>
    </div>
  );
}
