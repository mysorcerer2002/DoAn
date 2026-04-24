"use client";

import { PosTransactionForm } from "@/components/shared/pos-transaction-form";

export default function MerchantPosNewTransactionPage() {
  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Giao dịch / Tạo mới</p>
        <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
          Tạo giao dịch tích điểm
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Nhập thông tin để tích điểm cho khách hàng
        </p>
      </header>
      <div className="mt-6">
        <PosTransactionForm accentColor="indigo" />
      </div>
    </main>
  );
}
