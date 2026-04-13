"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Eye, EyeOff, Lock, Mail } from "lucide-react";

import { api, authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useTenantStore } from "@/lib/tenant-store";
import type { TenantStaffSummary } from "@/types/merchant";

const schema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const setTenant = useTenantStore((s) => s.setTenant);
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
      const res = await authApi.login(data);
      setTokens(res.data.access_token, res.data.refresh_token);
      await fetchMe();

      // Redirect theo role: super_admin → /admin, staff → /merchant, else → /member
      const user = useAuthStore.getState().user;
      if (user?.system_role === "super_admin") {
        router.push("/admin");
        return;
      }
      try {
        const { data: tenants } = await api.get<TenantStaffSummary[]>(
          "/users/me/tenants"
        );
        if (tenants.length > 0) {
          // Auto-select tenant đầu tiên để tránh hiển thị picker
          const t = tenants[0];
          setTenant({
            id: t.id,
            name: t.name,
            slug: t.slug,
            role: t.role,
          });
          router.push("/merchant");
          return;
        }
      } catch {
        // Ignore — treat as customer
      }
      router.push("/member");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Đăng nhập thất bại");
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
            Chào mừng
          </h1>
          <div className="w-10" />
        </header>

        <section className="flex h-[353px] w-full flex-col items-center justify-center bg-gradient-to-br from-brand-indigo to-brand-violet px-6 pt-16 text-center">
          <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-xl">
            <span className="font-headline text-4xl font-bold text-brand-indigo">
              L
            </span>
          </div>
          <h2 className="font-headline text-[24px] font-bold leading-tight text-white">
            Loyalty Platform
          </h2>
          <p className="mt-2 text-[14px] text-white/80">
            Tích điểm - Đổi quà - Nhận ưu đãi
          </p>
        </section>

        <main className="relative z-10 -mt-10 mb-12 px-5">
          <div className="rounded-3xl bg-white p-6 shadow-2xl">
            <div className="mb-8 flex items-center border-b border-slate-200">
              <div className="flex-1 border-b-2 border-brand-indigo pb-3 text-center">
                <span className="font-headline font-bold text-brand-indigo">
                  Đăng nhập
                </span>
              </div>
              <Link
                href="/register"
                className="flex-1 pb-3 text-center transition-colors hover:text-brand-indigo"
              >
                <span className="font-headline font-medium text-slate-500">
                  Đăng ký
                </span>
              </Link>
            </div>

            <div className="mb-6">
              <p className="text-base font-medium text-slate-500">
                Chào mừng quay lại!
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
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

              <div className="space-y-2">
                <div className="relative">
                  <Lock className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    autoComplete="current-password"
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
                <div className="flex justify-end">
                  <a
                    href="#"
                    className="text-sm font-medium text-brand-indigo hover:underline"
                  >
                    Quên mật khẩu?
                  </a>
                </div>
              </div>

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
                {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
              </button>

              <div className="relative flex items-center py-2">
                <div className="flex-grow border-t border-slate-200" />
                <span className="mx-4 flex-shrink text-sm font-medium text-slate-400">
                  hoặc
                </span>
                <div className="flex-grow border-t border-slate-200" />
              </div>

              <button
                type="button"
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-brand-indigo bg-white px-4 py-3.5 font-medium text-brand-indigo transition-all hover:bg-brand-indigo/5 active:scale-[0.98]"
              >
                <svg viewBox="0 0 24 24" className="h-5 w-5">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A11 11 0 0 0 1 12c0 1.78.43 3.46 1.18 4.93l3.66-2.84z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"
                  />
                </svg>
                <span>Đăng nhập với Google</span>
              </button>
            </form>
          </div>

          <div className="mt-8 text-center">
            <p className="font-body text-slate-500">
              Chưa có tài khoản?{" "}
              <Link
                href="/register"
                className="ml-1 font-bold text-brand-indigo hover:underline"
              >
                Đăng ký ngay
              </Link>
            </p>
          </div>

          <footer className="mt-16 px-8 text-center">
            <p className="text-[10px] leading-relaxed text-slate-400">
              Bằng việc đăng nhập, bạn đồng ý với{" "}
              <a href="#" className="underline">
                Điều khoản
              </a>{" "}
              &{" "}
              <a href="#" className="underline">
                Chính sách bảo mật
              </a>
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}
