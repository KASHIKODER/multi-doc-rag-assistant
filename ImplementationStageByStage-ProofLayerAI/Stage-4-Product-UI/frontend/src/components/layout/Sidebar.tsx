import Link from "next/link";
import { APP_CONFIG, NAV_ITEMS } from "@/lib/constants";

type SidebarProps = {
  activePath?: string;
};

export function Sidebar({ activePath = "/dashboard" }: SidebarProps) {
  return (
    <aside className="flex h-screen w-72 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-5">
        <Link href="/" className="block">
          <p className="text-sm font-semibold text-[#2563EB]">
            {APP_CONFIG.name}
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {APP_CONFIG.tagline}
          </p>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = activePath === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "block rounded-2xl px-4 py-3 transition",
                isActive
                  ? "bg-[#2563EB] text-white"
                  : "text-slate-700 hover:bg-slate-50 hover:text-[#0F172A]",
              ].join(" ")}
            >
              <span className="text-sm font-semibold">{item.label}</span>
              <span
                className={[
                  "mt-1 block text-xs leading-5",
                  isActive ? "text-white/80" : "text-slate-500",
                ].join(" ")}
              >
                {item.description}
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 px-6 py-5">
        <div className="rounded-2xl bg-[#10B981]/10 p-4">
          <p className="text-sm font-semibold text-[#0F172A]">
            Source-grounded
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            Answers are designed to stay tied to retrieved document context.
          </p>
        </div>
      </div>
    </aside>
  );
}
