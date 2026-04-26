"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, QrCode, Gift, Ticket, User } from "lucide-react";
import { cn } from "@/lib/utils";

const HOME_SUB_ROUTES = ["/member/history", "/member/partners"];

export function BottomNavBar() {
  const pathname = usePathname();

  if (pathname === "/member/qr") {
    return null;
  }

  if (/^\/member\/partners\/[^/]+/.test(pathname)) {
    return null;
  }

  if (/^\/member\/vouchers\/[^/]+/.test(pathname)) {
    return null;
  }

  const isHomeActive =
    pathname === "/member" ||
    HOME_SUB_ROUTES.some((route) => pathname.startsWith(route));
  const isRewardsActive = pathname.startsWith("/member/rewards");
  const isVouchersActive = pathname.startsWith("/member/vouchers");
  const isProfileActive = pathname.startsWith("/member/profile");
  const isQrActive = pathname === "/member/qr";

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex w-full items-end justify-around rounded-t-2xl border-t border-slate-100 bg-white/80 px-4 pt-3 pb-6 shadow-[0_-4px_12px_rgba(0,0,0,0.05)] backdrop-blur-md">
      <NavTab href="/member" icon={Home} label="Trang chủ" active={isHomeActive} />
      <NavTab
        href="/member/rewards"
        icon={Gift}
        label="Quà"
        active={isRewardsActive}
      />

      <Link href="/member/qr" className="flex flex-1 flex-col items-center -mt-8 pb-2">
        <div className="rounded-full bg-gradient-to-tr from-brand-indigo to-brand-violet p-4 shadow-lg shadow-indigo-200 transition-transform active:scale-90">
          <QrCode className="h-7 w-7 text-white" strokeWidth={2.5} />
        </div>
        <span
          className={cn(
            "mt-1 text-[12px] font-medium",
            isQrActive ? "text-brand-indigo" : "text-slate-500"
          )}
        >
          QR
        </span>
      </Link>

      <NavTab
        href="/member/vouchers"
        icon={Ticket}
        label="Voucher"
        active={isVouchersActive}
      />
      <NavTab
        href="/member/profile"
        icon={User}
        label="Tôi"
        active={isProfileActive}
      />
    </nav>
  );
}

function NavTab({
  href,
  icon: Icon,
  label,
  active,
}: {
  href: string;
  icon: typeof Home;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex flex-1 flex-col items-center justify-center gap-1 py-2 cursor-pointer transition-colors",
        active
          ? "font-semibold text-brand-indigo"
          : "text-slate-500 hover:text-brand-indigo"
      )}
    >
      <Icon
        className="h-6 w-6"
        fill={active ? "currentColor" : "none"}
        strokeWidth={active ? 1.5 : 2}
      />
      <span className="text-[12px] font-medium">{label}</span>
    </Link>
  );
}
