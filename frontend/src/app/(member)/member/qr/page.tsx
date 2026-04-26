"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { useEffect } from "react";
import { useMe } from "@/lib/hooks/use-me";

export default function MemberQRPage() {
  const router = useRouter();
  const { data: user, isLoading, isError } = useMe();

  useEffect(() => {
    if (isError) router.replace("/login");
  }, [isError, router]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <Link
          href="/member"
          className="-ml-2 flex h-11 w-11 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100"
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-base font-semibold">QR cá nhân</h1>
      </header>

      {isLoading || !user ? (
        <div className="flex min-h-[60vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center px-4 pt-10">
          <div className="rounded-3xl bg-white p-6 shadow-xl shadow-indigo-100">
            <QRCodeSVG
              value={user.id.toString()}
              size={240}
              level="H"
              bgColor="#ffffff"
              fgColor="#1e1b4b"
            />
          </div>
          {user.full_name && (
            <p className="mt-5 font-headline text-[18px] font-bold text-slate-800">
              {user.full_name}
            </p>
          )}
          <p className="mt-1 text-[13px] text-slate-500">
            Xuất trình QR này để nhân viên quét tích điểm.
          </p>
          <p className="mt-3 rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-500">
            Mã thành viên: {user.id}
          </p>
        </div>
      )}
    </div>
  );
}
