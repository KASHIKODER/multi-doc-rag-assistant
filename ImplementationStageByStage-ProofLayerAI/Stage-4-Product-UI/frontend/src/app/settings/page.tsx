import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { APP_ROUTES } from "@/lib/constants";

const retrievalSettings = [
  {
    label: "Query Routing",
    description: "Infer the target subject when the user asks an implicit question.",
    value: "Enabled",
  },
  {
    label: "Local Re-ranking",
    description: "Reorder retrieved chunks before sending context to the answer layer.",
    value: "Enabled",
  },
  {
    label: "Relevance Grading",
    description: "Filter weak chunks before generating citation-backed answers.",
    value: "Enabled",
  },
  {
    label: "Citation Repair",
    description: "Map claims back to retrieved sources when source numbers are weak.",
    value: "Enabled",
  },
];

const modelSettings = [
  {
    label: "Answer Engine",
    value: "Ollama local LLM",
  },
  {
    label: "Embedding Model",
    value: "HuggingFace sentence embeddings",
  },
  {
    label: "Vector Store",
    value: "Chroma",
  },
];

export default function SettingsPage() {
  return (
    <AppShell activePath={APP_ROUTES.settings} title="Settings">
      <PageHeader
        title="Settings"
        description="Manage workspace preferences and future retrieval controls. These settings are currently displayed as product-ready placeholders."
      />

      <section className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-[#2563EB]">Profile</p>

          <div className="mt-5 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#2563EB] text-base font-semibold text-white">
              SG
            </div>

            <div>
              <h2 className="text-lg font-semibold text-[#0F172A]">
                Suyash Giri
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Document intelligence workspace owner
              </p>
            </div>
          </div>

          <div className="mt-6 rounded-2xl bg-slate-50 p-4">
            <p className="text-xs font-medium text-slate-500">Account status</p>
            <p className="mt-1 text-sm font-semibold text-[#10B981]">
              Local demo mode
            </p>
          </div>

          <p className="mt-4 text-sm leading-6 text-slate-600">
            Google and GitHub authentication will be added in a later product
            stage. For now, this UI focuses on a clean workspace experience.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-[#2563EB]">
            Retrieval controls
          </p>

          <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
            RAG pipeline behavior
          </h2>

          <div className="mt-6 grid gap-3">
            {retrievalSettings.map((setting) => (
              <div
                key={setting.label}
                className="rounded-2xl border border-slate-200 p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-[#0F172A]">
                      {setting.label}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      {setting.description}
                    </p>
                  </div>

                  <span className="rounded-full bg-[#10B981]/10 px-3 py-1 text-xs font-semibold text-[#10B981]">
                    {setting.value}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <details className="mt-5 rounded-2xl border border-slate-200 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-[#0F172A]">
              Advanced model details
            </summary>

            <div className="mt-4 grid gap-3">
              {modelSettings.map((item) => (
                <div
                  key={item.label}
                  className="flex justify-between gap-4 text-sm"
                >
                  <span className="text-slate-500">{item.label}</span>
                  <span className="font-semibold text-[#0F172A]">
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </details>
        </div>
      </section>

      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold text-[#2563EB]">
          Future configuration
        </p>

        <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
          Settings that will become editable later
        </h2>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm font-semibold">Top K</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Control how many final chunks are passed to answer generation.
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm font-semibold">Candidate limit</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Control how many retrieved chunks enter the re-ranking stage.
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm font-semibold">Grading mode</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Switch between heuristic grading and LLM-based relevance grading.
            </p>
          </div>
        </div>
      </section>
    </AppShell>
  );
}
