import type { HTMLAttributes, ReactNode } from "react";

type BadgeVariant =
  | "primary"
  | "success"
  | "neutral"
  | "outline"
  | "muted";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode;
  variant?: BadgeVariant;
};

const variantClasses: Record<BadgeVariant, string> = {
  primary: "bg-[#2563EB]/10 text-[#2563EB]",
  success: "bg-[#10B981]/10 text-[#10B981]",
  neutral: "bg-slate-100 text-[#0F172A]",
  outline: "border border-slate-200 bg-white text-slate-600",
  muted: "bg-slate-50 text-slate-500",
};

export function Badge({
  children,
  variant = "neutral",
  className = "",
  ...props
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
        variantClasses[variant],
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </span>
  );
}
