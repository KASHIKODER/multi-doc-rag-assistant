import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { APP_ROUTES } from "@/lib/constants";

const pipelineSteps = [
  {
    id: 1,
    title: "Query Construction",
    description:
      "Transforms the user question into subject, module, and semantic query fields.",
  },
  {
    id: 2,
    title: "Query Routing",
    description:
      "Routes implicit questions to the most likely document subject when needed.",
  },
  {
    id: 3,
    title: "Candidate Retrieval",
    description:
      "Retrieves relevant chunks from the Chroma vector store using embeddings.",
  },
  {
    id: 4,
    title: "Local Re-ranking",
    description:
      "Reorders retrieved chunks using query overlap, metadata, and topic signals.",
  },
  {
    id: 5,
    title: "Relevance Grading",
    description:
      "Filters weak chunks before answer generation to improve grounding.",
  },
  {
    id: 6,
    title: "Source-Grounded Answer",
    description:
      "Returns topic answers or claim-level cited answers with source metadata.",
  },
];

const nextActions = [
  {
    title: "Review documents",
    description: "Inspect indexed PDFs, subjects, module numbers, and metadata.",
  },
  {
    title: "Ask a question",
    description: "Test topic answers, citation-backed answers, and routing.",
  },
  {
    title: "Review history",
    description: "Check locally saved questions, answer modes, and sources.",
  },
];

const apiEndpoints = [
  "GET /health",
  "GET /documents",
  "POST /documents/upload",
  "POST /documents/rebuild",
  "POST /ask",
];

const runtimeNotes = [
  "FastAPI bridges the UI with the Stage-2 Python RAG engine.",
  "Chroma DB stores indexed PDF chunks for retrieval.",
  "Pipeline details stay hidden until expanded by the user.",
];

export default function DeveloperPage() {
  return (
    <AppShell activePath={APP_ROUTES.developer} title="Developer">
      <PageHeader
        title="Developer"
        description="Inspect the source-grounded RAG pipeline and product architecture used by the workspace."
      />

      <section className="mt-5 grid items-start gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-[#2563EB]">
                System Flow
              </p>

              <h2 className="mt-2 text-2xl font-semibold text-[#0F172A]">
                Source-grounded retrieval pipeline
              </h2>
            </div>

            <Badge variant="success">Active</Badge>
          </div>

          <div className="mt-5 grid gap-3">
            {pipelineSteps.map((step) => (
              <div
                key={step.id}
                className="grid grid-cols-[2.75rem_1fr] gap-4 rounded-2xl border border-slate-200 p-4"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#2563EB] text-sm font-semibold text-white">
                  {step.id}
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
        </section>

        <aside className="grid gap-5">
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-[#2563EB]">
              Next Actions
            </p>

            <h2 className="mt-2 text-2xl font-semibold text-[#0F172A]">
              Continue building
            </h2>

            <div className="mt-5 grid gap-3">
              {nextActions.map((action) => (
                <div
                  key={action.title}
                  className="rounded-2xl border border-slate-200 p-4"
                >
                  <h3 className="text-sm font-semibold text-[#0F172A]">
                    {action.title}
                  </h3>

                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {action.description}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-[#2563EB]">
              API Surface
            </p>

            <h2 className="mt-2 text-2xl font-semibold text-[#0F172A]">
              FastAPI endpoints
            </h2>

            <div className="mt-5 grid gap-2">
              {apiEndpoints.map((endpoint) => (
                <div
                  key={endpoint}
                  className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3"
                >
                  <code className="text-sm font-semibold text-[#0F172A]">
                    {endpoint}
                  </code>

                  <span className="h-2.5 w-2.5 rounded-full bg-[#10B981]" />
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-[#2563EB]">
              Runtime Notes
            </p>

            <h2 className="mt-2 text-2xl font-semibold text-[#0F172A]">
              Local MVP behavior
            </h2>

            <div className="mt-5 grid gap-3">
              {runtimeNotes.map((note) => (
                <div
                  key={note}
                  className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600"
                >
                  {note}
                </div>
              ))}
            </div>
          </section>
        </aside>
      </section>
    </AppShell>
  );
}