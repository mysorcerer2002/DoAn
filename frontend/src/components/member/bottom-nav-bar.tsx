"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, QrCode, Gift, User } from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/member", icon: Home, label: "Trang chủ" },
  { href: "/member/rewards", icon: Gift, label: "Quà" },
  { href: "/member/profile", icon: User, label: "Tôi" },
] as const;

export function BottomNavBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex w-full items-end justify-around rounded-t-2xl border-t border-slate-100 bg-white/80 px-4 pt-3 pb-6 shadow-[0_-4px_12px_rgba(0,0,0,0.05)] backdrop-blur-md">
      {/* Trang chủ */}
      <NavTab
        href="/member"
        icon={Home}
        label="Trang chủ"
        active={pathname === "/member"}
      />

      {/* QR center, nổi lên */}
      <Link href="/member/qr" className="flex flex-col items-center -mt-8">
        <div className="rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 p-4 shadow-lg shadow-indigo-200 transition-transform active:scale-90">
          <QrCode className="h-7 w-7 text-white" strokeWidth={2.5} />
        </div>
        <span
          className={cn(
            "mt-1 text-[12px] font-medium",
            pathname === "/member/qr" ? "text-indigo-600" : "text-slate-400"
          )}
        >
          QR
        </span>
      </Link>

      <NavTab
        href="/member/rewards"
        icon={Gift}
        label="Quà"
        active={pathname.startsWith("/member/rewards")}
      />
      <NavTab
        href="/member/profile"
        icon={User}
        label="Tôi"
        active={pathname.startsWith("/member/profile")}
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
        "flex flex-col items-center gap-1 cursor-pointer transition-colors",
        active
          ? "font-semibold text-indigo-600"
          : "text-slate-400 hover:text-indigo-500"
      )}
    >
      <Icon
        className="h-6 w-6"
        fill={active ? "currentColor" : "none"}
        strokeWidth={active ? 0 : 2}
      />
      <span className="text-[12px] font-medium">{label}</span>
    </Link>
  );
}
