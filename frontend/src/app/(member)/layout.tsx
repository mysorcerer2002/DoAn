import type { ReactNode } from "react";
import { BottomNavBar } from "@/components/member/bottom-nav-bar";

export default function MemberLayout({ children }: { children: ReactNode }) {
  return (
    <div className="bg-[#f8fafc] min-h-screen pb-32 font-body text-slate-800">
      <div className="mx-auto max-w-md">{children}</div>
      <BottomNavBar />
    </div>
  );
}
