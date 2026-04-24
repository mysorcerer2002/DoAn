"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { MobileTopbar } from "@/components/shared/mobile-topbar";
import { StaffSidebar } from "@/components/staff/staff-sidebar";
import { useMe } from "@/lib/hooks/use-me";
import { usePartnerStore } from "@/lib/partner-store";

export default function StaffLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
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

  // Nếu user là owner, chuyển sang /partner (không nên ở /staff)
  useEffect(() => {
    if (mounted && tenant && tenant.role === "owner") {
      router.replace("/partner");
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

  if (!tenant) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4 text-center">
        <div className="max-w-md rounded-2xl border border-amber-200 bg-amber-50 p-6">
          <p className="font-bold text-amber-700">Chưa chọn cửa hàng</p>
          <p className="mt-2 text-[13px] text-amber-600">
            Bạn cần được owner thêm vào tenant_staff trước khi sử dụng cổng nhân
            viên.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <StaffSidebar />
      <div className="md:ml-60">
        <MobileTopbar title="Staff" gradientClass="bg-emerald-700" />
        {children}
      </div>
    </div>
  );
}
