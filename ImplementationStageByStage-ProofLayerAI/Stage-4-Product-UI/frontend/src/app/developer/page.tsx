import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { APP_ROUTES, PIPELINE_STEPS } from "@/lib/constants";

const systemCapabilities = [
  {
    title: "Metadata-aware retrieval",
    description:
      "Each chunk carries course metadata such as subject, module number, module title, topics, and key concepts.",
  },
  {
    title: "Implicit query routing",
    description:
      "Short questions like 'What are selectors?' can be routed to the right subject even when the user does not explicitly say CSS3.",
  },
  {
    title: "Context quality control",
    description:
      "Retrieved chunks are re-ranked and graded before they reach answer generation.",
  },
  {
    title: "Claim-level citation",
    description:
      "Generated claims are mapped back to retrieved document sources and shown with page-level metadata.",
  },
];

const responseShape = [
  "detected_subject",
  "semantic_query",
  "answer_mode",
  "retrieval_stats",
  "summary",
  "verified_claims",
  "sources",
];

export default function DeveloperPage() {
  return (
    <AppShell activePath={APP_ROUTES.developer} title="Developer">
      <PageHeader
        title="Developer Pipeline"
        description="A clean technical view of how the routed, re-ranked, and graded RAG system works under the product interface."
      />

      <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.85fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-[#2563EB]">
            Architecture flow
          </p>

          <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
            From question to verified answer
          </h2>

          <div className="mt-6 grid gap-4">
            {PIPELINE_STEPS.map((step, index) => (
              <div
                key={step.title}
                className="rounded-2xl border border-slate-200 p-4"
              >
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#2563EB] text-sm font-semibold text-white">
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
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-[#2563EB]">
              API-ready response
            </p>

            <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
              Planned response contract
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              When the FastAPI bridge is added, the frontend will render a clean
              response object instead of reading terminal output.
            </p>

            <div className="mt-5 grid gap-2">
              {responseShape.map((field) => (
                <div
                  key={field}
                  className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3"
                >
                  <span className="text-sm font-medium text-[#0F172A]">
                    {field}
                  </span>
                  <span className="h-2.5 w-2.5 rounded-full bg-[#10B981]" />
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-[#2563EB]">
              Backend status
            </p>

            <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
              Current engine
            </h2>

            <div className="mt-5 grid gap-3">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  RAG backend
                </p>
                <p className="mt-1 text-sm font-semibold text-[#0F172A]">
                  Python Stage-2 engine
                </p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  API bridge
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-500">
                  Planned in Stage 04C
                </p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  UI connection
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-500">
                  Planned in Stage 04D
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold text-[#2563EB]">
          System capabilities
        </p>

        <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
          What makes this more than a basic PDF chatbot
        </h2>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {systemCapabilities.map((capability) => (
            <div
              key={capability.title}
              className="rounded-2xl border border-slate-200 p-4"
            >
              <p className="text-sm font-semibold text-[#0F172A]">
                {capability.title}
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                {capability.description}
              </p>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
