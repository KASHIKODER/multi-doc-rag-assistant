import Link from "next/link";
import { UserMenu } from "@/components/auth/UserMenu";
import { APP_ROUTES } from "@/lib/constants";

type TopbarProps = {
  title?: string;
};

export function Topbar({ title = "Document Workspace" }: TopbarProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-[#F8FAFC]/90 px-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          Workspace
        </p>
        <h2 className="text-base font-semibold text-[#0F172A]">{title}</h2>
      </div>

      <div className="flex items-center gap-3">
        <Link
          href={APP_ROUTES.ask}
          className="rounded-xl bg-[#2563EB] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
        >
          Ask Documents
        </Link>

        <UserMenu />
      </div>
    </header>
  );
}