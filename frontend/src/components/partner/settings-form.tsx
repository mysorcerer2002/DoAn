"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import { useState } from "react";

import { useUpdatePointRule, useUpdateTier } from "@/lib/hooks/use-partner-settings";
import type { PointRuleResponse, TierResponse } from "@/types/partner";

// ==================== PointRuleForm ====================

interface PointRuleFormProps {
  rule: PointRuleResponse;
}

export function PointRuleForm({ rule }: PointRuleFormProps) {
  const updateRule = useUpdatePointRule(rule.id);

  const [earnPercent, setEarnPercent] = useState(rule.earn_percent);
  const [useTiers, setUseTiers] = useState(rule.use_tiers);
  const [status, setStatus] = useState<"idle" | "ok" | "err">("idle");

  const handleSave = async () => {
    if (!earnPercent || earnPercent < 0.01 || earnPercent > 99.99) {
      setStatus("err");
      return;
    }

    try {
      await updateRule.mutateAsync({
        earn_percent: earnPercent,
        use_tiers: useTiers,
      });
      setStatus("ok");
    } catch {
      setStatus("err");
    }
  };

  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <h2 className="font-headline text-[18px] font-bold text-slate-800">
        Cấu hình tích điểm
      </h2>
      <p className="mt-1 text-[12px] text-slate-500">
        Quy tắc quy đổi tiền mua hàng sang điểm thưởng
      </p>

      {status === "ok" && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-[13px] text-emerald-700">
          <CheckCircle2 className="h-4 w-4" />
          Đã lưu quy tắc tích điểm
        </div>
      )}
      {status === "err" && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-[13px] text-red-700">
          <XCircle className="h-4 w-4" />
          Lưu thất bại — kiểm tra lại giá trị nhập
        </div>
      )}

      <div className="mt-4 space-y-3">
        <div>
          <label className="text-[12px] font-medium text-slate-500">
            % tích điểm
          </label>
          <p className="mt-0.5 text-[11px] text-slate-400">
            Khách hàng nhận số điểm bằng tỷ lệ phần trăm này nhân với giá trị hóa đơn.
            Ví dụ: cài 1% thì hóa đơn 100.000đ sẽ tích được 1.000 điểm.
          </p>
          <div className="mt-1 flex items-center gap-2">
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="99.99"
              value={earnPercent}
              onChange={(e) => { setEarnPercent(parseFloat(e.target.value)); setStatus("idle"); }}
              className="w-32 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
              required
            />
            <span className="text-[13px] text-slate-500">%</span>
          </div>
        </div>

        <label className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-3">
          <div>
            <p className="text-[13px] font-bold text-slate-800">
              Áp dụng hệ số theo hạng thành viên
            </p>
            <p className="text-[11px] text-slate-500">
              {useTiers
                ? "Bật: áp hệ số theo hạng — khách hạng cao tích nhanh hơn."
                : "Tắt: mọi khách tích cùng tỉ lệ."}
            </p>
          </div>
          <input
            type="checkbox"
            checked={useTiers}
            onChange={(e) => { setUseTiers(e.target.checked); setStatus("idle"); }}
            className="h-5 w-5 rounded border-slate-300 text-brand-indigo"
          />
        </label>
      </div>

      <button
        type="button"
        onClick={handleSave}
        disabled={updateRule.isPending}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet py-2.5 text-[13px] font-bold text-white shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-60"
      >
        {updateRule.isPending ? "Đang lưu..." : "Lưu quy tắc tích điểm"}
      </button>
    </section>
  );
}

// ==================== TierMultiplierRow ====================

interface TierMultiplierRowProps {
  tier: TierResponse;
}

export function TierMultiplierRow({ tier }: TierMultiplierRowProps) {
  const updateTier = useUpdateTier();
  const [multiplier, setMultiplier] = useState(tier.earn_multiplier);
  const [status, setStatus] = useState<"idle" | "ok" | "err">("idle");

  const handleSave = async () => {
    const val = Number(multiplier);
    if (isNaN(val) || val < 0.5 || val > 5.0) {
      setStatus("err");
      return;
    }
    try {
      await updateTier.mutateAsync({
        id: tier.id,
        data: { earn_multiplier: val.toFixed(2) },
      });
      setStatus("ok");
    } catch {
      setStatus("err");
    }
  };

  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
      <div className="flex-1">
        <p className="text-[13px] font-bold text-slate-800">{tier.name}</p>
        <p className="text-[11px] text-slate-500">
          ≥ {tier.min_points.toLocaleString("vi-VN")} điểm
        </p>
      </div>
      <div className="flex items-center gap-2">
        {status === "ok" && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
        {status === "err" && <XCircle className="h-4 w-4 text-red-500" />}
        <span className="text-[12px] text-slate-500">×</span>
        <input
          type="number"
          min="0.50"
          max="5.00"
          step="0.01"
          value={multiplier}
          onChange={(e) => { setMultiplier(e.target.value); setStatus("idle"); }}
          className="w-20 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-center text-[13px] outline-none focus:border-brand-indigo focus:ring-2 focus:ring-brand-indigo/20"
        />
        <button
          type="button"
          onClick={handleSave}
          disabled={updateTier.isPending}
          className="rounded-xl bg-brand-indigo px-3 py-1.5 text-[12px] font-bold text-white hover:bg-brand-violet active:scale-95 disabled:opacity-60"
        >
          Lưu
        </button>
      </div>
    </div>
  );
}
