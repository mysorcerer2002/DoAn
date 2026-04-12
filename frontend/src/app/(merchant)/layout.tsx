import type { ReactNode } from "react";
import { MerchantSidebar } from "@/components/merchant/merchant-sidebar";

export default function MerchantLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#f8fafc] font-body text-slate-800">
      <MerchantSidebar />
      <div className="ml-60">{children}</div>
    </div>
  );
}
