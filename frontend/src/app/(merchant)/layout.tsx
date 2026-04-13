"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { MerchantSidebar } from "@/components/merchant/merchant-sidebar";
import { TenantPicker } from "@/components/merchant/tenant-picker";
import { MobileTopbar } from "@/components/shared/mobile-topbar";
import { useTenantStore } from "@/lib/tenant-store";
import { useMe } from "@/lib/hooks/use-me";

export default function MerchantLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const tenant = useTenantStore((s) => s.tenant);
  const rehydrate = useTenantStore((s) => s.rehydrate);
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

  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-slate-500">Đang tải...</div>
      </div>
    );
  }

  if (!user) return null;

  // Chưa chọn tenant → hiển thị picker (ngoại trừ trang picker chính nó)
  if (!tenant) {
    return (
      <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
        <TenantPicker targetHref={pathname} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <MerchantSidebar />
      <div className="md:ml-60">
        <MobileTopbar title="Merchant" gradientClass="bg-brand-indigo" />
        {children}
      </div>
    </div>
  );
}
