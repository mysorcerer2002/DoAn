"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  Shield,
  Store,
  Users,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect } from "react";

import { cn } from "@/lib/utils";
import { useLogout } from "@/lib/hooks/use-logout";
import { useSidebarStore } from "@/lib/sidebar-store";

type MenuItem = {
  href: string;
  icon: LucideIcon;
  label: string;
};

const menu: readonly MenuItem[] = [
  { href: "/admin", icon: LayoutDashboard, label: "Tổng quan" },
  { href: "/admin/tenants", icon: Store, label: "Đối tác" },
  { href: "/admin/users", icon: Users, label: "Người dùng" },
  { href: "/admin/templates", icon: FileText, label: "Template" },
  { href: "/admin/campaigns", icon: ClipboardList, label: "Duyệt chiến dịch" },
  { href: "/admin/campaigns/overdue", icon: AlertTriangle, label: "Quá hạn báo cáo" },
  { href: "/admin/stats", icon: BarChart3, label: "Thống kê" },
  { href: "/admin/audit", icon: Activity, label: "Nhật ký" },
  { href: "/admin/settings", icon: Settings, label: "Cài đặt" },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const open = useSidebarStore((s) => s.open);
  const close = useSidebarStore((s) => s.close);
  const logout = useLogout();

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
          "fixed left-0 top-0 z-30 flex h-screen w-64 flex-col bg-gradient-to-b from-indigo-900 to-violet-900 text-white transition-transform md:w-60 md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Menu điều hướng Admin"
      >
        <div className="px-5 pt-6">
          <div className="flex items-center justify-between gap-2.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white font-headline text-xl font-bold text-indigo-900">
                L
              </div>
              <div>
                <p className="font-headline text-[15px] font-bold">
                  Loyalty Admin
                </p>
                <p className="flex items-center gap-1 text-[10px] text-indigo-200">
                  <Shield className="h-2.5 w-2.5" />
                  Hệ thống nội bộ
                </p>
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

          <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-brand-orange to-amber-500 text-[12px] font-bold">
                ND
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-bold text-white">
                  Nguyễn Duy
                </p>
                <span className="inline-block rounded-full bg-brand-orange px-1.5 py-0.5 text-[9px] font-bold uppercase">
                  Super Admin
                </span>
              </div>
            </div>
          </div>
        </div>

        <nav className="mt-5 flex-1 space-y-1 overflow-y-auto px-3">
          {menu.map((item) => {
            const active =
              item.href === "/admin"
                ? pathname === "/admin"
                : pathname === item.href ||
                  pathname.startsWith(item.href + "/");
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
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl border border-white/20 px-3 py-2.5 text-[13px] font-medium text-indigo-100 transition-colors hover:bg-white/10 active:scale-[0.98]"
          >
            <LogOut className="h-5 w-5" />
            Đăng xuất
          </button>
        </div>
      </aside>
    </>
  );
}
