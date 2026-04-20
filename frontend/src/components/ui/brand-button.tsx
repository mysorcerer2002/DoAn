import type { ButtonHTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const baseClass =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-indigo to-brand-violet font-headline font-bold text-white shadow-lg shadow-indigo-200 transition-transform active:scale-[0.98] disabled:opacity-60";

const sizeClass = {
  sm: "px-4 py-2 text-[12px]",
  md: "px-5 py-2.5 text-[13px]",
  lg: "px-6 py-3 text-[14px]",
  xl: "py-4 text-[16px]",
} as const;

type Size = keyof typeof sizeClass;

type CommonProps = {
  size?: Size;
  fullWidth?: boolean;
  className?: string;
  children: ReactNode;
};

export type BrandButtonProps = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children">;

export function BrandButton({
  size = "md",
  fullWidth,
  className,
  children,
  ...props
}: BrandButtonProps) {
  return (
    <button
      type={props.type ?? "button"}
      className={cn(
        baseClass,
        sizeClass[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export type BrandLinkProps = CommonProps & {
  href: string;
};

export function BrandLink({
  size = "md",
  fullWidth,
  className,
  children,
  href,
}: BrandLinkProps) {
  return (
    <Link
      href={href}
      className={cn(
        baseClass,
        sizeClass[size],
        fullWidth && "w-full",
        className
      )}
    >
      {children}
    </Link>
  );
}
