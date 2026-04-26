"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { useAuthStore } from "@/lib/auth-store";

export default function MemberQRPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <Link
          href="/member"
          className="flex h-9 w-9 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-base font-semibold">QR cá nhân</h1>
      </header>

      {!user ? (
        <div className="p-4">Đang tải...</div>
      ) : (
        <div className="flex flex-col items-center justify-center px-4 pt-10">
          <div className="bg-white p-6 rounded-2xl shadow-lg">
            <QRCodeSVG value={user.id.toString()} size={240} level="H" />
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Xuất trình QR này để nhân viên quét tích điểm.
          </p>
          <p className="mt-2 text-xs text-muted-foreground">ID: {user.id}</p>
        </div>
      )}
    </div>
  );
}
