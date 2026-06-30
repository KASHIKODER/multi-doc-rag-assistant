import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { APP_ROUTES, PIPELINE_STEPS } from "@/lib/constants";

const overviewCards = [
  {
    label: "Indexed Documents",
    value: "5",
    description: "Course PDFs currently available in the local RAG workspace.",
  },
  {
    label: "Pipeline Stages",
    value: "6",
    description: "Construction, routing, retrieval, re-ranking, grading, answer.",
  },
  {
    label: "Answer Modes",
    value: "2",
    description: "Metadata topic answers and claim-level cited answers.",
  },
];

export default function DashboardPage() {
  return (
    <AppShell activePath={APP_ROUTES.dashboard} title="Dashboard">
      <PageHeader
        title="Dashboard"
        description="A clean overview of the document intelligence workspace and the current source-grounded RAG pipeline."
        action={
          <Link
            href={APP_ROUTES.ask}
            className="rounded-xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
          >
            Ask Documents
          </Link>
        }
      />

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        {overviewCards.map((card) => (
          <div
            key={card.label}
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <p className="text-sm font-medium text-slate-500">{card.label}</p>
            <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
              {card.value}
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              {card.description}
            </p>
          </div>
        ))}
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.85fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-[#2563EB]">
                System Flow
              </p>
              <h2 className="mt-2 text-xl font-semibold">
                Source-grounded retrieval pipeline
              </h2>
            </div>
            <span className="rounded-full bg-[#10B981]/10 px-3 py-1 text-sm font-semibold text-[#10B981]">
              Active
            </span>
          </div>

          <div className="mt-6 grid gap-3">
            {PIPELINE_STEPS.map((step, index) => (
              <div
                key={step.title}
                className="flex gap-4 rounded-2xl border border-slate-200 p-4"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#2563EB] text-sm font-semibold text-white">
                  {index + 1}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[#0F172A]">
                    {step.title}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-[#2563EB]">Next Actions</p>
          <h2 className="mt-2 text-xl font-semibold">Continue building</h2>

          <div className="mt-6 grid gap-3">
            <Link
              href={APP_ROUTES.documents}
              className="rounded-2xl border border-slate-200 p-4 transition hover:border-[#2563EB]"
            >
              <p className="text-sm font-semibold">Review documents</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Inspect indexed PDFs, subjects, module numbers, and metadata.
              </p>
            </Link>

            <Link
              href={APP_ROUTES.ask}
              className="rounded-2xl border border-slate-200 p-4 transition hover:border-[#2563EB]"
            >
              <p className="text-sm font-semibold">Ask a question</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Test topic answers, citation-backed answers, and routing.
              </p>
            </Link>

            <Link
              href={APP_ROUTES.developer}
              className="rounded-2xl border border-slate-200 p-4 transition hover:border-[#2563EB]"
            >
              <p className="text-sm font-semibold">Inspect pipeline</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                View the retrieval and answer-generation architecture.
              </p>
            </Link>
          </div>
        </div>
      </section>
    </AppShell>
  );
}
