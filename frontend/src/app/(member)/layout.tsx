"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { BottomNavBar } from "@/components/member/bottom-nav-bar";
import { usePartnerStore } from "@/lib/partner-store";

export default function MemberLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const partner = usePartnerStore((s) => s.activePartner);
  const rehydrate = usePartnerStore((s) => s.rehydrate);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    rehydrate();
  }, [rehydrate]);

  // Staff không có quyền vào /member → ép về /staff/pos
  useEffect(() => {
    if (mounted && partner && partner.role === "staff") {
      router.replace("/staff");
    }
  }, [mounted, partner, router]);

  return (
    <div className="bg-[#f8fafc] min-h-screen pb-32 font-body text-slate-800">
      <div className="mx-auto max-w-md">{children}</div>
      <BottomNavBar />
    </div>
  );
}
