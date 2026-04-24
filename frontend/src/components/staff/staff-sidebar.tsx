"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CreditCard, LayoutDashboard, LogOut, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect } from "react";

import { cn } from "@/lib/utils";
import { useLogout } from "@/lib/hooks/use-logout";
import { useSidebarStore } from "@/lib/sidebar-store";
import { usePartnerStore } from "@/lib/partner-store";

type MenuItem = {
  href: string;
  icon: LucideIcon;
  label: string;
};

const menu: readonly MenuItem[] = [
  { href: "/staff", icon: LayoutDashboard, label: "Tổng quan" },
  {
    href: "/staff/pos/transactions/new",
    icon: CreditCard,
    label: "Tạo giao dịch",
  },
];

export function StaffSidebar() {
  const pathname = usePathname();
  const open = useSidebarStore((s) => s.open);
  const close = useSidebarStore((s) => s.close);
  const logout = useLogout();
  const tenant = usePartnerStore((s) => s.tenant);

  useEffect(() => {
    close();
  }, [pathname, close]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [close]);

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-20 bg-slate-900/50 backdrop-blur-sm transition-opacity md:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={close}
        aria-hidden="true"
      />

      <aside
        className={cn(
          "fixed left-0 top-0 z-30 flex h-screen w-64 flex-col bg-gradient-to-b from-emerald-700 to-emerald-900 text-white transition-transform md:w-60 md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Menu nhân viên"
      >
        <div className="px-5 pt-6">
          <div className="flex items-center justify-between gap-2.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white font-headline text-xl font-bold text-emerald-700">
                S
              </div>
              <div>
                <p className="font-headline text-[15px] font-bold">Staff Portal</p>
                <p className="text-[10px] text-emerald-200">Nhân viên cửa hàng</p>
              </div>
            </div>
            <button
              type="button"
              onClick={close}
              className="flex h-8 w-8 items-center justify-center rounded-full text-white/70 hover:bg-white/10 md:hidden"
              aria-label="Đóng menu"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {tenant && (
            <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="truncate text-[10px] uppercase tracking-wider text-emerald-200">
                Cửa hàng
              </p>
              <p className="truncate text-[13px] font-bold text-white">
                {tenant.name}
              </p>
            </div>
          )}
        </div>

        <nav className="mt-5 flex-1 space-y-1 overflow-y-auto px-3">
          {menu.map((item) => {
            const active =
              item.href === "/staff"
                ? pathname === "/staff"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-colors",
                  active
                    ? "border-l-4 border-brand-orange bg-white/10 pl-2 font-bold text-white"
                    : "text-emerald-100 hover:bg-white/10"
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
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl border border-white/20 px-3 py-2.5 text-[13px] font-medium text-emerald-100 transition-colors hover:bg-white/10 active:scale-[0.98]"
          >
            <LogOut className="h-5 w-5" />
            Đăng xuất
          </button>
        </div>
      </aside>
    </>
  );
}
