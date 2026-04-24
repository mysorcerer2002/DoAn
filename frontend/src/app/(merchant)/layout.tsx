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
  const tenant = usePartnerStore((s) => s.tenant);
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

  // Staff không có quyền vào /merchant → redirect /staff
  useEffect(() => {
    if (mounted && tenant && tenant.role === "staff") {
      router.replace("/staff");
    }
  }, [mounted, tenant, router]);

  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-slate-500">Đang tải...</div>
      </div>
    );
  }

  if (!user) return null;

  // Chưa chọn partner → hiển thị picker (ngoại trừ trang picker chính nó)
  if (!tenant) {
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
        <MobileTopbar title="Merchant" gradientClass="bg-brand-indigo" />
        {children}
      </div>
    </div>
  );
}
