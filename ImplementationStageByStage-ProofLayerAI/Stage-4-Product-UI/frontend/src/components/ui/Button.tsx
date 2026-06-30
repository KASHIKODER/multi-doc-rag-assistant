import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "subtle" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
};

const baseClasses =
  "inline-flex items-center justify-center font-semibold transition outline-none disabled:cursor-not-allowed disabled:opacity-60";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[#2563EB] text-white shadow-sm hover:opacity-90 focus:ring-2 focus:ring-[#2563EB]/20",
  secondary:
    "border border-slate-200 bg-white text-[#0F172A] hover:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/20",
  subtle:
    "bg-[#10B981]/10 text-[#0F172A] hover:bg-[#10B981]/15 focus:ring-2 focus:ring-[#10B981]/20",
  ghost:
    "bg-transparent text-slate-600 hover:bg-slate-100 hover:text-[#0F172A] focus:ring-2 focus:ring-slate-200",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "rounded-lg px-3 py-2 text-xs",
  md: "rounded-xl px-5 py-2.5 text-sm",
  lg: "rounded-2xl px-6 py-3 text-sm",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  fullWidth = false,
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  const widthClass = fullWidth ? "w-full" : "";

  return (
    <button
      type={type}
      className={[
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        widthClass,
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
