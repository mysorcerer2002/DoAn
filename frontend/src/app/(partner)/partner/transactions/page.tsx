"use client";

import { useState } from "react";
import { Search } from "lucide-react";

import { usePartnerStore } from "@/lib/partner-store";
import { usePartnerTransactions } from "@/lib/hooks/use-partner-transactions";
import { TransactionTable } from "@/components/partner/transaction-table";
import { TransactionDetailSheet } from "@/components/partner/transaction-detail-sheet";

const PAGE_SIZE = 20;

export default function PartnerTransactionsPage() {
  const role = usePartnerStore((s) => s.activePartner?.role);
  const isOwner = role === "owner";

  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const txnQ = usePartnerTransactions({
    page,
    page_size: PAGE_SIZE,
    q: q.trim() || undefined,
  });

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header className="flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="font-headline text-[28px] font-bold text-slate-800 md:text-[32px]">
            Lịch sử giao dịch
          </h1>
          <p className="mt-1 text-[13px] text-slate-500">
            Toàn bộ giao dịch POS của đối tác
          </p>
        </div>
        <div className="relative w-full md:w-64">
          <Search className="pointer-events-none absolute inset-y-0 left-3 my-auto h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            placeholder="Tìm mã hoá đơn..."
            className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
          />
        </div>
      </header>

      <div className="mt-5">
        {txnQ.isLoading && (
          <p className="text-[13px] text-slate-500">Đang tải...</p>
        )}
        {txnQ.isError && (
          <p className="rounded-xl bg-rose-50 px-3 py-2 text-[13px] text-rose-600">
            Không tải được danh sách. Thử lại sau.
          </p>
        )}
        {txnQ.data && (
          <TransactionTable
            items={txnQ.data.items}
            total={txnQ.data.total}
            page={txnQ.data.page}
            pageSize={txnQ.data.page_size}
            onPageChange={setPage}
            onRowClick={setSelectedId}
          />
        )}
      </div>

      <TransactionDetailSheet
        transactionId={selectedId}
        isOwner={isOwner}
        open={selectedId !== null}
        onClose={() => setSelectedId(null)}
      />
    </main>
  );
}
