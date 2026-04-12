import {
  ArrowLeft,
  Bell,
  Calendar,
  ChevronRight,
  Crown,
  Globe,
  HelpCircle,
  Lock,
  LogOut,
  Mail,
  MapPin,
  Pencil,
  Phone,
  ScrollText,
  Settings,
  Shield,
} from "lucide-react";
import Link from "next/link";

const infoItems = [
  { id: "phone", icon: Phone, label: "Số điện thoại", value: "0987 654 321" },
  { id: "email", icon: Mail, label: "Email", value: "minhanh@email.com" },
  {
    id: "birthday",
    icon: Calendar,
    label: "Ngày sinh",
    value: "15/03/1998",
  },
  { id: "address", icon: MapPin, label: "Địa chỉ", value: "Hai Bà Trưng, HN" },
] as const;

const settingsItems = [
  { id: "notif", icon: Bell, label: "Thông báo", trailing: "toggle" },
  { id: "lang", icon: Globe, label: "Ngôn ngữ", trailing: "Tiếng Việt" },
  { id: "password", icon: Lock, label: "Đổi mật khẩu", trailing: "chevron" },
  {
    id: "help",
    icon: HelpCircle,
    label: "Trợ giúp & Hỗ trợ",
    trailing: "chevron",
  },
] as const;

const otherItems = [
  { id: "terms", icon: ScrollText, label: "Điều khoản sử dụng" },
  { id: "privacy", icon: Shield, label: "Chính sách bảo mật" },
] as const;

export default function ProfilePage() {
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
            className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-transform hover:bg-white/10 active:scale-95"
            aria-label="Cài đặt"
          >
            <Settings className="h-6 w-6" />
          </button>
        </div>

        <div className="relative z-10 mt-3 flex flex-col items-center">
          <div className="relative">
            <div className="flex h-24 w-24 items-center justify-center rounded-full border-4 border-white bg-gradient-to-br from-indigo-200 to-violet-200 text-2xl font-bold text-indigo-700 shadow-lg">
              MA
            </div>
            <button
              type="button"
              className="absolute bottom-0 right-0 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white bg-brand-orange text-white shadow-md"
              aria-label="Đổi ảnh đại diện"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
          </div>
          <h2 className="mt-3 font-headline text-[24px] font-bold text-white">
            Nguyễn Minh Anh
          </h2>
          <div className="mt-1 flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-400 px-3 py-1 shadow-lg">
            <Crown className="h-3.5 w-3.5 text-white" fill="white" />
            <span className="font-headline text-[12px] font-bold text-white">
              Hạng Vàng
            </span>
          </div>
          <p className="mt-1 text-[12px] text-white/70">
            Thành viên từ 03/2025
          </p>
        </div>
      </header>

      <main className="-mt-8 space-y-5 px-4">
        <section className="grid grid-cols-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-lg">
          <Stat value="2.450" label="Điểm hiện có" valueColor="orange" />
          <Stat value="8" label="Cửa hàng" valueColor="indigo" border />
          <Stat value="12" label="Voucher" valueColor="indigo" />
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <h3 className="font-headline text-[16px] font-bold text-slate-800">
              Thông tin cá nhân
            </h3>
            <button
              type="button"
              className="flex items-center gap-1 text-[13px] font-semibold text-brand-indigo"
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
                className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-slate-50"
                style={
                  idx > 0
                    ? { borderTop: "1px solid #f1f5f9" }
                    : undefined
                }
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
                <ChevronRight className="h-5 w-5 text-slate-300" />
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h3 className="px-1 font-headline text-[16px] font-bold text-slate-800">
            Cài đặt
          </h3>
          <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
            {settingsItems.map((item, idx) => (
              <div
                key={item.id}
                className="flex items-center gap-3 px-4 py-3.5"
                style={
                  idx > 0
                    ? { borderTop: "1px solid #f1f5f9" }
                    : undefined
                }
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
                  <item.icon className="h-5 w-5 text-brand-indigo" />
                </div>
                <p className="flex-1 text-[14px] font-medium text-slate-800">
                  {item.label}
                </p>
                {item.trailing === "toggle" && (
                  <span className="inline-flex h-6 w-11 items-center rounded-full bg-brand-indigo p-0.5">
                    <span className="ml-auto h-5 w-5 rounded-full bg-white shadow" />
                  </span>
                )}
                {item.trailing === "Tiếng Việt" && (
                  <span className="text-[13px] text-slate-400">
                    Tiếng Việt
                  </span>
                )}
                {item.trailing === "chevron" && (
                  <ChevronRight className="h-5 w-5 text-slate-300" />
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h3 className="px-1 font-headline text-[16px] font-bold text-slate-800">
            Khác
          </h3>
          <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
            {otherItems.map((item, idx) => (
              <button
                key={item.id}
                type="button"
                className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-slate-50"
                style={
                  idx > 0
                    ? { borderTop: "1px solid #f1f5f9" }
                    : undefined
                }
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
                  <item.icon className="h-5 w-5 text-brand-indigo" />
                </div>
                <p className="flex-1 text-[14px] font-medium text-slate-800">
                  {item.label}
                </p>
                <ChevronRight className="h-5 w-5 text-slate-300" />
              </button>
            ))}
            <button
              type="button"
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
    </>
  );
}

function Stat({
  value,
  label,
  valueColor,
  border,
}: {
  value: string;
  label: string;
  valueColor: "orange" | "indigo";
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
          valueColor === "orange"
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
