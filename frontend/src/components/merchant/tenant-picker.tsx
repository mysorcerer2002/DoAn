"use client";

import { useQuery } from "@tanstack/react-query";
import { Store } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { api } from "@/lib/api";
import { useTenantStore } from "@/lib/tenant-store";
import type { TenantStaffSummary } from "@/types/merchant";

/** Tự động set active tenant nếu user chỉ có 1 shop, hoặc show picker. */
export function TenantPicker({ targetHref }: { targetHref: string }) {
  const router = useRouter();
  const { tenant: activeTenant, setTenant } = useTenantStore();

  const { data: tenants, isLoading } = useQuery<TenantStaffSummary[]>({
    queryKey: ["users", "me", "tenants"],
    queryFn: async () => {
      const res = await api.get<TenantStaffSummary[]>("/users/me/tenants");
      return res.data;
    },
  });

  useEffect(() => {
    if (activeTenant) {
      router.replace(targetHref);
      return;
    }
    if (tenants && tenants.length === 1) {
      const t = tenants[0];
      setTenant({ id: t.id, name: t.name, slug: t.slug, role: t.role });
      router.replace(targetHref);
    }
  }, [tenants, activeTenant, setTenant, router, targetHref]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-slate-500">Đang tải danh sách cửa hàng...</div>
      </div>
    );
  }

  if (!tenants || tenants.length === 0) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
        <Store className="mx-auto h-12 w-12 text-slate-400" />
        <h2 className="mt-4 font-headline text-[18px] font-bold text-slate-800">
          Bạn chưa tham gia cửa hàng nào
        </h2>
        <p className="mt-2 text-[13px] text-slate-500">
          Đăng ký doanh nghiệp mới hoặc chờ lời mời từ chủ shop.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto mt-16 max-w-md space-y-4 px-4">
      <h1 className="font-headline text-[24px] font-bold text-slate-800">
        Chọn cửa hàng
      </h1>
      <ul className="space-y-2">
        {tenants.map((t) => (
          <li key={t.id}>
            <button
              type="button"
              onClick={() => {
                setTenant({ id: t.id, name: t.name, slug: t.slug, role: t.role });
                router.replace(targetHref);
              }}
              className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-brand-indigo hover:bg-brand-indigo/5"
            >
              <div>
                <p className="font-bold text-slate-800">{t.name}</p>
                <p className="text-[12px] text-slate-500">
                  {t.slug} · {t.role}
                </p>
              </div>
              <span className="rounded-full bg-indigo-50 px-3 py-1 text-[11px] font-bold text-brand-indigo">
                Chọn
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
