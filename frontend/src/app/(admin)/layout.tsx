"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { AdminSidebar } from "@/components/admin/admin-sidebar";
import { MobileTopbar } from "@/components/shared/mobile-topbar";
import { useMe } from "@/lib/hooks/use-me";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const { data: user, isLoading, isError } = useMe();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (isError) {
      router.replace("/login");
      return;
    }
    if (!isLoading && user && user.system_role !== "super_admin") {
      router.replace("/login");
    }
  }, [mounted, isError, isLoading, user, router]);

  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-slate-500">Đang tải...</div>
      </div>
    );
  }

  if (!user || user.system_role !== "super_admin") return null;

  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <AdminSidebar />
      <div className="md:ml-60">
        <MobileTopbar title="Admin" gradientClass="bg-indigo-900" />
        {children}
      </div>
    </div>
  );
}
