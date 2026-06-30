import type { HTMLAttributes, ReactNode } from "react";

type CardPadding = "none" | "sm" | "md" | "lg";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  padding?: CardPadding;
};

const paddingClasses: Record<CardPadding, string> = {
  none: "p-0",
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

export function Card({
  children,
  padding = "lg",
  className = "",
  ...props
}: CardProps) {
  return (
    <div
      className={[
        "rounded-3xl border border-slate-200 bg-white shadow-sm",
        paddingClasses[padding],
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}

type CardHeaderProps = HTMLAttributes<HTMLDivElement> & {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
};

export function CardHeader({
  eyebrow,
  title,
  description,
  action,
  className = "",
  ...props
}: CardHeaderProps) {
  return (
    <div
      className={[
        "flex flex-col gap-4 md:flex-row md:items-start md:justify-between",
        className,
      ].join(" ")}
      {...props}
    >
      <div>
        {eyebrow ? (
          <p className="text-sm font-semibold text-[#2563EB]">{eyebrow}</p>
        ) : null}

        <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
          {title}
        </h2>

        {description ? (
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
            {description}
          </p>
        ) : null}
      </div>

      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
