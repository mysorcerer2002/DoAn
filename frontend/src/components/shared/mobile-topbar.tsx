"use client";

import { Menu } from "lucide-react";

import { useSidebarStore } from "@/lib/sidebar-store";

interface MobileTopbarProps {
  title: string;
  /** Tailwind class cho background gradient/color */
  gradientClass?: string;
}

/** Top bar chỉ hiển thị trên mobile/tablet (< md). Chứa nút hamburger mở sidebar. */
export function MobileTopbar({
  title,
  gradientClass = "bg-brand-indigo",
}: MobileTopbarProps) {
  const toggle = useSidebarStore((s) => s.toggle);

  return (
    <header
      className={`sticky top-0 z-10 flex h-14 items-center gap-3 ${gradientClass} px-4 text-white shadow-md md:hidden`}
    >
      <button
        type="button"
        onClick={toggle}
        className="flex h-10 w-10 items-center justify-center rounded-xl hover:bg-white/10"
        aria-label="Mở menu"
      >
        <Menu className="h-6 w-6" />
      </button>
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white font-headline text-sm font-bold text-brand-indigo">
          L
        </div>
        <p className="font-headline text-[14px] font-bold">{title}</p>
      </div>
    </header>
  );
}
