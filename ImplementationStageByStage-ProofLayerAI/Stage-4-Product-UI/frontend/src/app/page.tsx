import Link from "next/link";
import { APP_CONFIG, APP_ROUTES } from "@/lib/constants";

const features = [
  "Multi-document retrieval",
  "Query routing",
  "Re-ranked context",
  "Source-backed answers",
];

export default function LandingPage() {
  return (
    <main className="h-screen overflow-hidden bg-[#F8FAFC] text-[#0F172A]">
      <section className="mx-auto flex h-full w-full max-w-7xl flex-col px-6 py-6">
        <header className="flex shrink-0 items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <p className="text-sm font-semibold text-[#2563EB]">
              {APP_CONFIG.name}
            </p>

            <h1 className="mt-1 text-xl font-semibold">
              Document Intelligence Workspace
            </h1>
          </div>

          <Link
            href={APP_ROUTES.dashboard}
            className="rounded-xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
          >
            Open Dashboard
          </Link>
        </header>

        <div className="grid min-h-0 flex-1 items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
          <section className="min-w-0">
            <div className="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700">
              Routed · Re-ranked · Source-grounded
            </div>

            <h2 className="mt-5 max-w-4xl text-5xl font-semibold leading-[1.08] tracking-tight">
              Ask across your documents and get verified answers.
            </h2>

            <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600">
              DocuMind turns course PDFs into a clean workspace. It routes the
              question, retrieves relevant context, verifies evidence, and
              displays source-backed claims.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href={APP_ROUTES.ask}
                className="rounded-xl bg-[#2563EB] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
              >
                Ask Documents
              </Link>

              <Link
                href={APP_ROUTES.developer}
                className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-[#0F172A] transition hover:border-[#2563EB]"
              >
                View Pipeline
              </Link>
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  Example Question
                </p>

                <h3 className="mt-2 text-xl font-semibold">
                  What are selectors?
                </h3>
              </div>

              <span className="rounded-full bg-[#10B981]/10 px-4 py-1.5 text-sm font-semibold text-[#10B981]">
                Verified
              </span>
            </div>

            <div className="mt-5 rounded-2xl bg-slate-50 p-5">
              <p className="text-sm font-semibold text-[#2563EB]">
                Detected Subject: CSS3
              </p>

              <p className="mt-3 text-base leading-7 text-slate-700">
                Selectors are used to target and style HTML elements. The
                retrieved CSS3 module covers universal, element, class, and ID
                selectors.
              </p>
            </div>

            <div className="mt-5 grid gap-3">
              {features.map((feature) => (
                <div
                  key={feature}
                  className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3"
                >
                  <span className="text-sm font-medium">{feature}</span>
                  <span className="h-2.5 w-2.5 rounded-full bg-[#10B981]" />
                </div>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}