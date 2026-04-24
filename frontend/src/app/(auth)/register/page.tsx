"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ArrowLeft,
  Eye,
  EyeOff,
  Lock,
  Mail,
  User as UserIcon,
} from "lucide-react";

import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const schema = z.object({
  full_name: z.string().min(1, "Họ tên không được để trống"),
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await authApi.register(data);
      setTokens(res.data.access_token, res.data.refresh_token);
      await fetchMe();
      router.push("/member");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Đăng ký thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <div className="relative mx-auto max-w-md">
        <header className="absolute top-0 left-0 z-50 flex h-16 w-full items-center justify-between bg-transparent px-4">
          <Link
            href="/"
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-transform hover:bg-white/10 active:scale-95"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <h1 className="font-headline text-lg font-bold text-white">
            Tạo tài khoản
          </h1>
          <div className="w-10" />
        </header>

        <section className="flex h-[300px] w-full flex-col items-center justify-center bg-gradient-to-br from-brand-indigo to-brand-violet px-6 pt-16 text-center">
          <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-xl">
            <span className="font-headline text-4xl font-bold text-brand-indigo">
              L
            </span>
          </div>
          <h2 className="font-headline text-[24px] font-bold leading-tight text-white">
            Tham gia Loyalty
          </h2>
          <p className="mt-2 text-[14px] text-white/80">
            Nhận 100 điểm chào mừng khi đăng ký
          </p>
        </section>

        <main className="relative z-10 -mt-10 mb-12 px-5">
          <div className="rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-8 flex items-center border-b border-slate-200">
              <Link
                href="/login"
                className="flex-1 pb-3 text-center transition-colors hover:text-brand-indigo"
              >
                <span className="font-headline font-medium text-slate-500">
                  Đăng nhập
                </span>
              </Link>
              <div className="flex-1 border-b-2 border-brand-indigo pb-3 text-center">
                <span className="font-headline font-bold text-brand-indigo">
                  Đăng ký
                </span>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-base font-medium text-slate-500">
                Tạo tài khoản chỉ mất 30 giây
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div className="space-y-1">
                <div className="relative">
                  <UserIcon className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Họ và tên"
                    autoComplete="name"
                    className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-10 pr-3 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
                    {...register("full_name")}
                  />
                </div>
                {errors.full_name && (
                  <p className="pl-1 text-xs text-red-500">
                    {errors.full_name.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Mail className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
                  <input
                    type="email"
                    placeholder="email@example.com"
                    autoComplete="email"
                    className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-10 pr-3 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
                    {...register("email")}
                  />
                </div>
                {errors.email && (
                  <p className="pl-1 text-xs text-red-500">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Lock className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="Tối thiểu 8 ký tự"
                    autoComplete="new-password"
                    className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-10 pr-10 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 hover:text-slate-600"
                    aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="pl-1 text-xs text-red-500">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <p className="rounded-lg bg-indigo-50 px-3 py-2 text-[11px] text-brand-indigo">
                Bạn có thể cập nhật ngày sinh trong trang Hồ sơ sau khi đăng ký
                để nhận voucher sinh nhật hàng năm.
              </p>

              {error && (
                <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-4 font-headline text-base font-bold text-white shadow-lg shadow-indigo-200 transition-transform active:scale-[0.98] disabled:opacity-60"
              >
                {submitting ? "Đang tạo tài khoản..." : "Đăng ký ngay"}
              </button>

              <p className="text-center text-xs text-slate-400">
                Bằng việc đăng ký, bạn đồng ý với{" "}
                <a href="#" className="font-medium text-brand-indigo hover:underline">
                  Điều khoản
                </a>{" "}
                &{" "}
                <a href="#" className="font-medium text-brand-indigo hover:underline">
                  Chính sách bảo mật
                </a>
              </p>
            </form>
          </div>

          <div className="mt-6 space-y-3 text-center">
            <p className="font-body text-slate-500">
              Đã có tài khoản?{" "}
              <Link
                href="/login"
                className="ml-1 font-bold text-brand-indigo hover:underline"
              >
                Đăng nhập
              </Link>
            </p>
            <Link
              href="/register/partner"
              className="inline-flex items-center gap-2 rounded-full border border-brand-indigo/30 bg-white px-4 py-2 text-[12px] font-bold text-brand-indigo transition hover:bg-indigo-50"
            >
              🏪 Bạn là chủ shop? Đăng ký bán hàng
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
