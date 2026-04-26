"use client";

import { Loader2, Coins, TrendingUp, TrendingDown, Settings } from "lucide-react";
import { useSystemPoints } from "@/lib/hooks/useSystemPoints";

export default function SystemPointsPage() {
  const { data, isLoading, isError } = useSystemPoints();

  if (isLoading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-indigo" />
      </main>
    );
  }

  if (isError || !data) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center px-8">
        <p className="text-red-600">Không tải được dữ liệu điểm hệ thống</p>
      </main>
    );
  }

  const summaryCards = [
    {
      label: "Điểm lưu hành",
      value: data.total_circulating,
      icon: Coins,
      bg: "bg-indigo-50 text-brand-indigo",
      desc: "Tổng điểm trong ví active users",
    },
    {
      label: "Đã tích luỹ",
      value: data.total_earned,
      icon: TrendingUp,
      bg: "bg-green-50 text-green-600",
      desc: "Tổng điểm earn qua giao dịch",
    },
    {
      label: "Đã đổi thưởng",
      value: data.total_redeemed,
      icon: TrendingDown,
      bg: "bg-orange-50 text-brand-orange",
      desc: "Tổng điểm đã dùng để đổi quà",
    },
    {
      label: "Đã điều chỉnh",
      value: data.total_adjusted,
      icon: Settings,
      bg: "bg-violet-50 text-brand-violet",
      desc: "Tổng delta từ admin adjustment",
    },
  ];

  return (
    <main className="px-4 py-5 md:px-8 md:py-6">
      <header>
        <p className="text-[12px] text-slate-400">Hệ thống / Quản lý điểm</p>
        <h1 className="mt-1 font-headline text-[32px] font-bold text-slate-800">
          Điểm hệ thống
        </h1>
        <p className="mt-1 text-[14px] text-slate-500">
          Tổng quan điểm toàn nền tảng Loyalty Platform
        </p>
      </header>

      {/* 4 stat cards */}
      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card) => (
          <article
            key={card.label}
            className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"
          >
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl ${card.bg}`}
            >
              <card.icon className="h-5 w-5" />
            </div>
            <p className="mt-4 text-[12px] font-medium text-slate-400">
              {card.label}
            </p>
            <p className="mt-1 font-headline text-[28px] font-bold text-slate-800">
              {card.value.toLocaleString("vi-VN")}
            </p>
            <p className="mt-1 text-[11px] text-slate-400">{card.desc}</p>
          </article>
        ))}
      </section>

      {/* Breakdown by partner */}
      <section className="mt-6">
        <h2 className="mb-4 font-headline text-[18px] font-bold text-slate-800">
          Điểm tích luỹ theo đối tác
        </h2>
        {data.by_partner.length === 0 ? (
          <p className="text-[13px] text-slate-400">Chưa có dữ liệu</p>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-sm">
            <table className="w-full text-[13px]">
              <thead className="border-b border-slate-100 bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-5 py-3 text-left font-semibold">Partner ID</th>
                  <th className="px-5 py-3 text-left font-semibold">Tên đối tác</th>
                  <th className="px-5 py-3 text-right font-semibold">Tổng điểm đã tích</th>
                </tr>
              </thead>
              <tbody>
                {data.by_partner.map((row) => (
                  <tr
                    key={row.partner_id}
                    className="border-b border-slate-50 hover:bg-slate-50"
                  >
                    <td className="px-5 py-3 text-slate-400">#{row.partner_id}</td>
                    <td className="px-5 py-3 font-medium text-slate-800">{row.name}</td>
                    <td className="px-5 py-3 text-right font-bold text-brand-indigo">
                      {row.total_earned.toLocaleString("vi-VN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
