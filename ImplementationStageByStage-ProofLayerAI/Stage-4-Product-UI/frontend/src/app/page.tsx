const features = [
  "Multi-document retrieval",
  "Query routing",
  "Re-ranked context",
  "Source-backed answers",
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8">
        <nav className="flex items-center justify-between border-b border-slate-200 pb-5">
          <div>
            <p className="text-sm font-semibold text-[#2563EB]">DocuMind RAG</p>
            <h1 className="text-xl font-semibold tracking-tight">
              Document Intelligence Workspace
            </h1>
          </div>

          <a
            href="/dashboard"
            className="rounded-xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
          >
            Open Dashboard
          </a>
        </nav>

        <div className="grid flex-1 items-center gap-10 py-16 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="mb-4 inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600">
              Routed · Re-ranked · Source-grounded
            </p>

            <h2 className="max-w-3xl text-5xl font-semibold leading-tight tracking-tight">
              Ask questions across your documents and get answers with verified
              sources.
            </h2>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              DocuMind turns course PDFs into a clean document workspace. It
              understands the question, retrieves the right context, verifies
              relevance, and shows source-backed claims.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="/ask"
                className="rounded-xl bg-[#2563EB] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
              >
                Ask Documents
              </a>

              <a
                href="/developer"
                className="rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-[#0F172A] transition hover:border-[#2563EB]"
              >
                View Pipeline
              </a>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  Example Question
                </p>
                <h3 className="mt-1 text-lg font-semibold">
                  What are selectors?
                </h3>
              </div>

              <span className="rounded-full bg-[#10B981]/10 px-3 py-1 text-sm font-semibold text-[#10B981]">
                Verified
              </span>
            </div>

            <div className="rounded-2xl bg-slate-50 p-5">
              <p className="text-sm font-semibold text-[#2563EB]">
                Detected Subject: CSS3
              </p>
              <p className="mt-3 text-slate-700">
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
          </div>
        </div>
      </section>
    </main>
  );
}
