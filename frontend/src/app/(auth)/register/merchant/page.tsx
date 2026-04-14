"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  Coffee,
  Eye,
  EyeOff,
  ImageIcon,
  Lock,
  Mail,
  MapPin,
  Palette,
  Phone,
  Sparkles,
  Store,
  User as UserIcon,
  UtensilsCrossed,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { api, authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const accountSchema = z.object({
  full_name: z.string().min(1, "Họ tên không được để trống"),
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
});

const shopSchema = z.object({
  name: z.string().min(2, "Tên shop tối thiểu 2 ký tự").max(255),
  category: z.enum(["cafe", "food", "retail", "beauty", "other"]),
  description: z.string().max(1000).optional().or(z.literal("")),
  logo_url: z
    .string()
    .url("URL không hợp lệ")
    .max(500)
    .optional()
    .or(z.literal("")),
  contact_phone: z
    .string()
    .min(8, "Số điện thoại tối thiểu 8 chữ số")
    .max(20)
    .regex(/^[0-9+\-\s()]+$/, "Số điện thoại không hợp lệ"),
  contact_email: z.string().email("Email không hợp lệ").max(255),
  address: z.string().min(5, "Địa chỉ tối thiểu 5 ký tự").max(500),
});

type AccountForm = z.infer<typeof accountSchema>;
type ShopForm = z.infer<typeof shopSchema>;

const CATEGORIES = [
  { id: "cafe", label: "Cafe", icon: Coffee },
  { id: "food", label: "Ẩm thực", icon: UtensilsCrossed },
  { id: "retail", label: "Bán lẻ", icon: Store },
  { id: "beauty", label: "Làm đẹp", icon: Palette },
  { id: "other", label: "Khác", icon: Building2 },
] as const;

export default function MerchantRegisterPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [account, setAccount] = useState<AccountForm | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const accountForm = useForm<AccountForm>({
    resolver: zodResolver(accountSchema),
  });
  const shopForm = useForm<ShopForm>({
    resolver: zodResolver(shopSchema),
    defaultValues: { category: "cafe" },
  });

  const handleAccountSubmit = (data: AccountForm) => {
    setAccount(data);
    setStep(2);
  };

  const handleShopSubmit = async (data: ShopForm) => {
    if (!account) return;
    setError(null);
    setSubmitting(true);
    try {
      const reg = await authApi.register({
        full_name: account.full_name,
        email: account.email,
        password: account.password,
      });
      setTokens(reg.data.access_token, reg.data.refresh_token);
      await fetchMe();

      await api.post("/merchant/register", {
        name: data.name,
        category: data.category,
        description: data.description || null,
        logo_url: data.logo_url || null,
        contact_phone: data.contact_phone,
        contact_email: data.contact_email,
        address: data.address,
      });

      setStep(3);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || "Đăng ký thất bại, vui lòng thử lại");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <div className="relative mx-auto max-w-md">
        {/* Header */}
        <header className="absolute top-0 left-0 z-50 flex h-16 w-full items-center justify-between bg-transparent px-4">
          <button
            type="button"
            onClick={() => {
              if (step === 1) router.push("/register");
              else if (step === 2) setStep(1);
            }}
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-transform hover:bg-white/10 active:scale-95"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-6 w-6" />
          </button>
          <h1 className="font-headline text-lg font-bold text-white">
            {step === 3 ? "Hoàn tất" : "Đăng ký Shop"}
          </h1>
          <div className="w-10" />
        </header>

        {/* Hero */}
        <section className="flex h-[280px] w-full flex-col items-center justify-center bg-gradient-to-br from-brand-indigo via-indigo-600 to-brand-violet px-6 pt-16 text-center">
          <div className="absolute right-6 top-20 h-24 w-24 rounded-full bg-white/10 blur-2xl" />
          <div className="absolute left-4 top-32 h-16 w-16 rounded-full bg-amber-300/20 blur-xl" />

          <div className="mb-3 flex h-20 w-20 items-center justify-center rounded-2xl bg-white shadow-2xl">
            {step === 3 ? (
              <CheckCircle2 className="h-10 w-10 text-emerald-500" />
            ) : (
              <Store className="h-10 w-10 text-brand-indigo" />
            )}
          </div>
          <h2 className="font-headline text-[24px] font-bold leading-tight text-white">
            {step === 3 ? "Đăng ký thành công" : "Mở shop trên Loyalty"}
          </h2>
          <p className="mt-2 max-w-xs text-[13px] text-white/85">
            {step === 3
              ? "Shop của bạn đang chờ admin duyệt"
              : "Tạo tài khoản chủ shop, quản lý khách hàng & chương trình tích điểm"}
          </p>

          {/* Progress dots */}
          {step < 3 && (
            <div className="mt-5 flex items-center gap-2">
              {[1, 2].map((s) => (
                <span
                  key={s}
                  className={
                    s === step
                      ? "h-2 w-8 rounded-full bg-white"
                      : s < step
                        ? "h-2 w-2 rounded-full bg-white"
                        : "h-2 w-2 rounded-full bg-white/40"
                  }
                />
              ))}
            </div>
          )}
        </section>

        <main className="relative z-10 -mt-10 mb-12 px-5">
          {step === 1 && (
            <div className="rounded-3xl bg-white p-6 shadow-2xl">
              <div className="mb-5">
                <p className="text-[11px] font-bold uppercase tracking-wider text-brand-indigo">
                  Bước 1 / 2
                </p>
                <h3 className="mt-1 font-headline text-[18px] font-bold text-slate-800">
                  Tài khoản chủ shop
                </h3>
                <p className="mt-1 text-[12px] text-slate-500">
                  Email và mật khẩu này dùng để đăng nhập quản lý shop
                </p>
              </div>

              <form
                onSubmit={accountForm.handleSubmit(handleAccountSubmit)}
                className="space-y-4"
              >
                <Field
                  icon={UserIcon}
                  placeholder="Họ và tên"
                  type="text"
                  autoComplete="name"
                  register={accountForm.register("full_name")}
                  error={accountForm.formState.errors.full_name?.message}
                />
                <Field
                  icon={Mail}
                  placeholder="email@shop.vn"
                  type="email"
                  autoComplete="email"
                  register={accountForm.register("email")}
                  error={accountForm.formState.errors.email?.message}
                />
                <div className="space-y-1">
                  <div className="relative">
                    <Lock className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
                    <input
                      type={showPassword ? "text" : "password"}
                      placeholder="Tối thiểu 8 ký tự"
                      autoComplete="new-password"
                      className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-10 pr-10 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/30"
                      {...accountForm.register("password")}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 hover:text-slate-600"
                      aria-label={
                        showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"
                      }
                    >
                      {showPassword ? (
                        <EyeOff className="h-5 w-5" />
                      ) : (
                        <Eye className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                  {accountForm.formState.errors.password && (
                    <p className="pl-1 text-xs text-red-500">
                      {accountForm.formState.errors.password.message}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3.5 font-headline text-[14px] font-bold text-white shadow-lg shadow-indigo-200 transition-transform active:scale-[0.98]"
                >
                  Tiếp tục
                  <ArrowRight className="h-4 w-4" />
                </button>
              </form>
            </div>
          )}

          {step === 2 && (
            <div className="rounded-3xl bg-white p-6 shadow-2xl">
              <div className="mb-5">
                <p className="text-[11px] font-bold uppercase tracking-wider text-brand-indigo">
                  Bước 2 / 2
                </p>
                <h3 className="mt-1 font-headline text-[18px] font-bold text-slate-800">
                  Thông tin shop
                </h3>
                <p className="mt-1 text-[12px] text-slate-500">
                  Khách hàng sẽ thấy các thông tin này khi khám phá shop
                </p>
              </div>

              <form
                onSubmit={shopForm.handleSubmit(handleShopSubmit)}
                className="space-y-4"
              >
                <Field
                  icon={Store}
                  placeholder="Tên shop (VD: Cafe Phố Cổ)"
                  type="text"
                  register={shopForm.register("name")}
                  error={shopForm.formState.errors.name?.message}
                />

                {/* Category picker */}
                <div>
                  <p className="mb-2 pl-1 text-[12px] font-bold text-slate-700">
                    Loại hình kinh doanh
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {CATEGORIES.map((cat) => {
                      const Icon = cat.icon;
                      const active = shopForm.watch("category") === cat.id;
                      return (
                        <button
                          key={cat.id}
                          type="button"
                          onClick={() =>
                            shopForm.setValue("category", cat.id, {
                              shouldValidate: true,
                            })
                          }
                          className={
                            active
                              ? "flex flex-col items-center gap-1.5 rounded-xl border-2 border-brand-indigo bg-indigo-50 px-2 py-3 transition"
                              : "flex flex-col items-center gap-1.5 rounded-xl border-2 border-slate-200 bg-white px-2 py-3 transition hover:border-slate-300"
                          }
                        >
                          <Icon
                            className={
                              active
                                ? "h-5 w-5 text-brand-indigo"
                                : "h-5 w-5 text-slate-400"
                            }
                          />
                          <span
                            className={
                              active
                                ? "text-[11px] font-bold text-brand-indigo"
                                : "text-[11px] font-medium text-slate-500"
                            }
                          >
                            {cat.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="relative">
                    <Sparkles className="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
                    <textarea
                      placeholder="Mô tả ngắn về shop (không bắt buộc)"
                      rows={3}
                      className="block w-full resize-none rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 text-[13px] outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/30"
                      {...shopForm.register("description")}
                    />
                  </div>
                  {shopForm.formState.errors.description && (
                    <p className="pl-1 text-xs text-red-500">
                      {shopForm.formState.errors.description.message}
                    </p>
                  )}
                </div>

                <Field
                  icon={ImageIcon}
                  placeholder="Logo URL (không bắt buộc)"
                  type="url"
                  register={shopForm.register("logo_url")}
                  error={shopForm.formState.errors.logo_url?.message}
                />

                {/* Contact section divider */}
                <div className="!mt-6 border-t border-dashed border-slate-200 pt-4">
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100">
                      <Phone className="h-3.5 w-3.5 text-brand-indigo" />
                    </span>
                    <h4 className="font-headline text-[13px] font-bold text-slate-800">
                      Thông tin liên hệ
                    </h4>
                  </div>
                  <p className="mb-3 pl-9 text-[11px] text-slate-500">
                    Khách hàng sẽ thấy thông tin này để liên hệ shop
                  </p>
                </div>

                <Field
                  icon={Phone}
                  placeholder="Số điện thoại shop (VD: 0901234567)"
                  type="tel"
                  autoComplete="tel"
                  register={shopForm.register("contact_phone")}
                  error={shopForm.formState.errors.contact_phone?.message}
                />

                <Field
                  icon={Mail}
                  placeholder="Email liên hệ (VD: hello@shop.vn)"
                  type="email"
                  autoComplete="email"
                  register={shopForm.register("contact_email")}
                  error={shopForm.formState.errors.contact_email?.message}
                />

                <div className="space-y-1">
                  <div className="relative">
                    <MapPin className="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
                    <textarea
                      placeholder="Địa chỉ shop (số nhà, đường, quận, thành phố)"
                      rows={2}
                      className="block w-full resize-none rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 text-[13px] outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/30"
                      {...shopForm.register("address")}
                    />
                  </div>
                  {shopForm.formState.errors.address && (
                    <p className="pl-1 text-xs text-red-500">
                      {shopForm.formState.errors.address.message}
                    </p>
                  )}
                </div>

                {error && (
                  <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3.5 font-headline text-[14px] font-bold text-white shadow-lg shadow-indigo-200 transition-transform active:scale-[0.98] disabled:opacity-60"
                >
                  {submitting ? "Đang đăng ký..." : "Tạo shop"}
                  {!submitting && <CheckCircle2 className="h-4 w-4" />}
                </button>
              </form>
            </div>
          )}

          {step === 3 && (
            <div className="rounded-3xl bg-white p-6 text-center shadow-2xl">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle2 className="h-9 w-9 text-emerald-600" />
              </div>
              <h3 className="mt-4 font-headline text-[20px] font-bold text-slate-800">
                Đăng ký hoàn tất
              </h3>
              <p className="mt-2 text-[13px] leading-relaxed text-slate-600">
                Shop của bạn đã được gửi cho admin xét duyệt.
                <br />
                Chúng tôi sẽ phản hồi trong vòng <strong>24 giờ</strong>.
              </p>

              <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-left">
                <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700">
                  Tiếp theo
                </p>
                <ul className="mt-2 space-y-1.5 text-[12px] text-amber-900">
                  <li>• Chuẩn bị logo, mô tả chi tiết shop</li>
                  <li>• Kiểm tra email để biết kết quả duyệt</li>
                  <li>• Sau khi duyệt, vào dashboard quản lý shop</li>
                </ul>
              </div>

              <Link
                href="/login"
                className="mt-5 flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-3.5 font-headline text-[14px] font-bold text-white shadow-lg shadow-indigo-200"
              >
                Về trang đăng nhập
              </Link>
            </div>
          )}

          {step < 3 && (
            <div className="mt-6 text-center">
              <p className="text-[13px] text-slate-500">
                Đã có shop?{" "}
                <Link
                  href="/login"
                  className="font-bold text-brand-indigo hover:underline"
                >
                  Đăng nhập
                </Link>
              </p>
              <p className="mt-2 text-[12px] text-slate-400">
                Bạn là khách hàng?{" "}
                <Link
                  href="/register"
                  className="font-bold text-brand-orange hover:underline"
                >
                  Đăng ký tài khoản thường
                </Link>
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function Field({
  icon: Icon,
  placeholder,
  type,
  autoComplete,
  register,
  error,
}: {
  icon: typeof Mail;
  placeholder: string;
  type: string;
  autoComplete?: string;
  register: ReturnType<ReturnType<typeof useForm>["register"]>;
  error?: string;
}) {
  return (
    <div className="space-y-1">
      <div className="relative">
        <Icon className="pointer-events-none absolute inset-y-0 left-3 my-auto h-5 w-5 text-slate-400" />
        <input
          type={type}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className="block w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-10 pr-3 outline-none transition-all placeholder:text-slate-400 focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/30"
          {...register}
        />
      </div>
      {error && <p className="pl-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
