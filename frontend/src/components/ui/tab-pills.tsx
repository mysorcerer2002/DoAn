"use client";

import { cn } from "@/lib/utils";

export type TabPillItem = {
  id: string;
  label: string;
  badge?: string;
};

type TabPillsProps = {
  items: readonly TabPillItem[];
  activeId: string;
  onChange?: (id: string) => void;
  variant?: "pills" | "underline";
  className?: string;
};

export function TabPills({
  items,
  activeId,
  onChange,
  variant = "pills",
  className,
}: TabPillsProps) {
  if (variant === "underline") {
    return (
      <nav
        className={cn(
          "flex items-center gap-6 border-b border-slate-200",
          className
        )}
      >
        {items.map((item) => {
          const active = item.id === activeId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onChange?.(item.id)}
              className={cn(
                "flex items-center gap-1.5 px-1 pb-3 text-[14px] transition-colors",
                active
                  ? "border-b-2 border-brand-indigo font-bold text-brand-indigo"
                  : "font-medium text-slate-500 hover:text-brand-indigo"
              )}
            >
              {item.label}
              {item.badge && (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[9px] font-bold",
                    active
                      ? "bg-brand-orange text-white"
                      : "bg-slate-200 text-slate-600"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    );
  }

  return (
    <nav className={cn("flex flex-wrap items-center gap-2", className)}>
      {items.map((item) => {
        const active = item.id === activeId;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange?.(item.id)}
            className={cn(
              "flex items-center gap-2 rounded-full px-4 py-2 text-[12px] transition-colors",
              active
                ? "bg-brand-indigo font-bold text-white"
                : "border border-slate-200 bg-white font-medium text-slate-500 hover:border-brand-indigo hover:text-brand-indigo"
            )}
          >
            {item.label}
            {item.badge && (
              <span
                className={cn(
                  "rounded-full px-1.5 py-0.5 text-[9px] font-bold",
                  active
                    ? "bg-brand-orange text-white"
                    : "bg-slate-200 text-slate-600"
                )}
              >
                {item.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
