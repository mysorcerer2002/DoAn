"use client";

import { QRCodeSVG } from "qrcode.react";
import { useAuthStore } from "@/lib/auth-store";

export default function MemberQRPage() {
  const user = useAuthStore((s) => s.user);
  if (!user) return <div className="p-4">Đang tải...</div>;

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-4">
      <h1 className="text-xl font-semibold mb-4">QR cá nhân của bạn</h1>
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <QRCodeSVG value={user.id.toString()} size={240} level="H" />
      </div>
      <p className="mt-4 text-sm text-muted-foreground">
        Xuất trình QR này để nhân viên quét tích điểm.
      </p>
      <p className="mt-2 text-xs text-muted-foreground">ID: {user.id}</p>
    </div>
  );
}
