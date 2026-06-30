import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

type AppShellProps = {
  children: ReactNode;
  activePath?: string;
  title?: string;
};

export function AppShell({
  children,
  activePath = "/dashboard",
  title = "Document Workspace",
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      <div className="flex min-h-screen">
        <Sidebar activePath={activePath} />

        <div className="flex min-h-screen flex-1 flex-col">
          <Topbar title={title} />

          <main className="flex-1 px-6 py-6">
            <div className="mx-auto w-full max-w-6xl">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
