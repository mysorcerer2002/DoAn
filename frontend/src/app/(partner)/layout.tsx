"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { PartnerSidebar } from "@/components/partner/partner-sidebar";
import { PartnerPicker } from "@/components/partner/partner-picker";
import { MobileTopbar } from "@/components/shared/mobile-topbar";
import { usePartnerStore } from "@/lib/partner-store";
import { useMe } from "@/lib/hooks/use-me";

export default function MerchantLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const partner = usePartnerStore((s) => s.activePartner);
  const rehydrate = usePartnerStore((s) => s.rehydrate);
  const [mounted, setMounted] = useState(false);
  const { data: user, isLoading, isError } = useMe();

  useEffect(() => {
    setMounted(true);
    rehydrate();
  }, [rehydrate]);

  useEffect(() => {
    if (mounted && isError) {
      router.replace("/login");
    }
  }, [mounted, isError, router]);

  useEffect(() => {
    if (mounted && !isLoading && !user && !isError) {
      router.replace("/login");
    }
  }, [mounted, isLoading, user, isError, router]);

  // Staff không có quyền vào /partner → redirect /staff
  useEffect(() => {
    if (mounted && partner && partner.role === "staff") {
      router.replace("/staff");
    }
  }, [mounted, partner, router]);

  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-slate-500">Đang tải...</div>
      </div>
    );
  }

  if (!user) return null;

  // Chưa chọn partner → hiển thị picker (ngoại trừ trang picker chính nó)
  if (!partner) {
    return (
      <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
        <PartnerPicker targetHref={pathname} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <PartnerSidebar />
      <div className="md:ml-60">
        <MobileTopbar title="Đối tác" gradientClass="bg-brand-indigo" />
        {children}
      </div>
    </div>
  );
}
