import type { LucideIcon } from "lucide-react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

const toneMap = {
  indigo: "bg-indigo-50 text-brand-indigo",
  orange: "bg-orange-50 text-brand-orange",
  green: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
  slate: "bg-slate-100 text-slate-600",
  red: "bg-red-50 text-red-600",
} as const;

export type StatTone = keyof typeof toneMap;

export type StatCardProps = {
  icon: LucideIcon;
  label: string;
  value: string;
  tone?: StatTone;
  trend?: {
    value: string;
    direction: "up" | "down";
  };
  sub?: string;
  variant?: "default" | "compact";
  highlightValue?: boolean;
};

export function StatCard({
  icon: Icon,
  label,
  value,
  tone = "indigo",
  trend,
  sub,
  variant = "default",
  highlightValue = false,
}: StatCardProps) {
  if (variant === "compact") {
    return (
      <article className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
            toneMap[tone]
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-[11px] text-slate-400">{label}</p>
          <p
            className={cn(
              "font-headline text-[22px] font-bold leading-tight",
              highlightValue || tone === "orange"
                ? "text-brand-orange"
                : "text-slate-800"
            )}
          >
            {value}
          </p>
        </div>
      </article>
    );
  }

  return (
    <article className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl",
            toneMap[tone]
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        {trend && (
          <span
            className={cn(
              "flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold",
              trend.direction === "up"
                ? "bg-emerald-50 text-emerald-600"
                : "bg-red-50 text-red-600"
            )}
          >
            {trend.direction === "up" ? (
              <ArrowUp className="h-3 w-3" />
            ) : (
              <ArrowDown className="h-3 w-3" />
            )}
            {trend.value}
          </span>
        )}
      </div>
      <p className="mt-4 text-[12px] font-medium text-slate-400">{label}</p>
      <p
        className={cn(
          "mt-1 font-headline text-[28px] font-bold leading-tight",
          highlightValue || tone === "orange"
            ? "text-brand-orange"
            : "text-slate-800"
        )}
      >
        {value}
      </p>
      {sub && (
        <p className="mt-1 text-[11px] text-slate-400">
          {sub}
        </p>
      )}
    </article>
  );
}
