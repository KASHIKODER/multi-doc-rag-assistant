import { UserMenu } from "@/components/auth/UserMenu";

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

      <UserMenu />
    </header>
  );
}