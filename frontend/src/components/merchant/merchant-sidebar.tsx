"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CreditCard,
  Gift,
  LogOut,
  Megaphone,
  Settings,
  Ticket,
  Users,
  UsersRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type MenuItem = {
  href: string;
  icon: LucideIcon;
  label: string;
};

const menu: readonly MenuItem[] = [
  { href: "/merchant", icon: BarChart3, label: "Dashboard" },
  {
    href: "/merchant/pos/transactions/new",
    icon: CreditCard,
    label: "Giao dịch",
  },
  { href: "/merchant/members", icon: Users, label: "Thành viên" },
  { href: "/merchant/rewards", icon: Gift, label: "Phần thưởng" },
  { href: "/merchant/campaigns", icon: Megaphone, label: "Chiến dịch" },
  { href: "/merchant/vouchers", icon: Ticket, label: "Voucher" },
  { href: "/merchant/staff", icon: UsersRound, label: "Nhân viên" },
  { href: "/merchant/settings", icon: Settings, label: "Cài đặt" },
];

export function MerchantSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-60 flex-col bg-brand-indigo text-white">
      <div className="px-5 pt-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white font-headline text-xl font-bold text-brand-indigo">
            L
          </div>
          <div>
            <p className="font-headline text-[15px] font-bold">Loyalty Platform</p>
            <p className="text-[10px] text-indigo-200">Merchant Dashboard</p>
          </div>
        </div>

        <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-[12px] font-bold">
              LB
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-bold text-white">
                Lê Văn Bình
              </p>
              <p className="truncate text-[10px] text-indigo-200">
                Cafe Cộng - Bà Triệu
              </p>
            </div>
          </div>
        </div>
      </div>

      <nav className="mt-5 flex-1 space-y-1 px-3 overflow-y-auto">
        {menu.map((item) => {
          const active =
            item.href === "/merchant"
              ? pathname === "/merchant"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-colors",
                active
                  ? "border-l-4 border-brand-orange bg-white/10 pl-2 font-bold text-white"
                  : "text-indigo-100 hover:bg-white/10"
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 px-3 py-4">
        <button
          type="button"
          className="flex w-full items-center gap-3 rounded-xl border border-white/20 px-3 py-2.5 text-[13px] font-medium text-indigo-100 transition-colors hover:bg-white/10"
        >
          <LogOut className="h-5 w-5" />
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}
