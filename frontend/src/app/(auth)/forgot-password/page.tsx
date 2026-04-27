"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Mail } from "lucide-react";

import { authApi } from "@/lib/api";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError(null);

    const trimmed = email.trim();
    if (!trimmed) {
      setEmailError("Vui lòng nhập email");
      return;
    }
    if (!EMAIL_RE.test(trimmed)) {
      setEmailError("Email không hợp lệ");
      return;
    }

    setSubmitting(true);
    try {
      await authApi.forgotPassword(trimmed);
      setSuccess(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <div className="relative mx-auto max-w-md">
        <header className="absolute top-0 left-0 z-50 flex h-16 w-full items-center justify-between bg-transparent px-4">
          <Link
            href="/login"
            className="flex h-11 w-11 items-center justify-center rounded-full text-white transition-transform hover:bg-white/10 active:scale-95"
            aria-label="Quay lại đăng nhập"
          >
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <h1 className="font-headline text-lg font-bold text-white">
            Quên mật khẩu
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
            Đặt lại mật khẩu của bạn
          </p>
        </section>

        <main className="relative z-10 -mt-10 mb-12 px-5">
          <div className="rounded-3xl bg-white p-6 shadow-2xl">
            {success ? (
              <div className="space-y-5 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <Mail className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <p className="font-headline text-[16px] font-bold text-slate-800">
                    Kiểm tra hộp thư của bạn
                  </p>
                  <p className="mt-2 text-[14px] text-slate-500">
                    Nếu email tồn tại trong hệ thống, mật khẩu tạm thời đã được
                    gửi. Vui lòng đăng nhập và đổi mật khẩu ngay sau khi nhận
                    được.
                  </p>
                </div>
                <Link
                  href="/login"
                  className="block w-full rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-4 font-headline text-base font-bold text-white shadow-lg shadow-indigo-200 text-center"
                >
                  Quay lại đăng nhập
                </Link>
              </div>
            ) : (
              <>
                <div className="mb-6">
                  <p className="text-[14px] text-slate-500">
                    Nhập email đã đăng ký, chúng tôi sẽ gửi mật khẩu tạm thời
                    để bạn đăng nhập lại.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-1">
                    <div className="relative">
                      <Mail className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
                      <input
                        type="email"
                        inputMode="email"
                        placeholder="Email của bạn"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => {
                          setEmail(e.target.value);
                          if (emailError) setEmailError(null);
                        }}
                        className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-10 pr-3 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo"
                      />
                    </div>
                    {emailError && (
                      <p className="pl-1 text-xs text-red-500">{emailError}</p>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-4 font-headline text-base font-bold text-white shadow-lg shadow-indigo-200 transition-transform active:scale-[0.98] disabled:opacity-60"
                  >
                    {submitting ? "Đang gửi..." : "Gửi mật khẩu tạm thời"}
                  </button>
                </form>

                <div className="mt-5 text-center">
                  <Link
                    href="/login"
                    className="text-sm font-medium text-brand-indigo hover:underline"
                  >
                    Quay lại đăng nhập
                  </Link>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
