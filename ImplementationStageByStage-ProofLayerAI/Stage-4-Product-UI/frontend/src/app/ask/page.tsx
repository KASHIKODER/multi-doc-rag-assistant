"use client";

import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { QuestionInput } from "@/components/chat/QuestionInput";
import { PipelineStats } from "@/components/chat/PipelineStats";
import { AnswerCard } from "@/components/chat/AnswerCard";
import { SourceCard } from "@/components/chat/SourceCard";
import { useRagWorkspace } from "@/components/rag/RagWorkspaceProvider";
import { APP_ROUTES, DEMO_QUESTIONS } from "@/lib/constants";
import type { RagAnswer } from "@/types/rag";

function answerModeLabel(mode: RagAnswer["answerMode"]) {
  if (mode === "citation") return "Citation-backed";
  if (mode === "topic") return "Topic answer";
  return "Unsupported";
}

function answerModeVariant(mode: RagAnswer["answerMode"]) {
  if (mode === "citation") return "success";
  if (mode === "topic") return "primary";
  return "muted";
}

export default function AskPage() {
  const {
    question,
    answer,
    loading,
    error,
    historyMessage,
    updateQuestion,
    runQuestion,
  } = useRagWorkspace();

  return (
    <AppShell activePath={APP_ROUTES.ask} title="Ask Documents">
      <PageHeader
        title="Ask Documents"
        description="Ask natural questions across indexed course PDFs and view source-grounded answers with verified claims."
      />

      <section className="mt-5 grid items-start gap-5 xl:grid-cols-[1fr_0.44fr]">
        <div className="grid gap-5">
          <QuestionInput
            value={question}
            onChange={updateQuestion}
            onSubmit={runQuestion}
            loading={loading}
            demoQuestions={DEMO_QUESTIONS}
          />

          {historyMessage ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold text-[#10B981]">
                History updated
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {historyMessage} You can review this question from the History
                page.
              </p>
            </section>
          ) : null}

          {error ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold text-[#2563EB]">
                Backend error
              </p>
              <p className="mt-3 text-sm leading-6 text-slate-700">{error}</p>
              <p className="mt-3 text-xs leading-5 text-slate-500">
                Make sure the FastAPI server is running on
                http://127.0.0.1:8000.
              </p>
            </section>
          ) : null}

          {loading ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold text-[#2563EB]">
                Running RAG pipeline
              </p>

              <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
                Retrieving, re-ranking, grading, and generating answer...
              </h2>

              <p className="mt-3 text-sm leading-6 text-slate-600">
                You can move to another section while the request continues.
                When you return, the latest answer will stay available.
              </p>
            </section>
          ) : null}

          {answer ? (
            <>
              <AnswerCard answer={answer} />

              <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-[#2563EB]">
                      Retrieved sources
                    </p>

                    <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
                      Context used for this answer
                    </h2>
                  </div>

                  <Badge variant="outline">{answer.sources.length} sources</Badge>
                </div>

                {answer.sources.length > 0 ? (
                  <div className="mt-5 grid gap-4 lg:grid-cols-2">
                    {answer.sources.map((source) => (
                      <SourceCard key={source.id} source={source} />
                    ))}
                  </div>
                ) : (
                  <div className="mt-5 rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm leading-6 text-slate-600">
                      No retrieved sources were returned for this answer.
                    </p>
                  </div>
                )}
              </section>
            </>
          ) : null}
        </div>

        <aside className="grid gap-5 self-start">
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-[#2563EB]">
              Query understanding
            </p>

            <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
              Parsed question state
            </h2>

            {answer ? (
              <>
                <div className="mt-4 grid gap-3">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs font-medium text-slate-500">
                      Detected subject
                    </p>

                    <div className="mt-2">
                      {answer.detectedSubject ? (
                        <Badge variant="primary">{answer.detectedSubject}</Badge>
                      ) : (
                        <Badge variant="muted">None</Badge>
                      )}
                    </div>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs font-medium text-slate-500">
                      Detected module
                    </p>

                    <p className="mt-1 text-sm font-semibold text-[#0F172A]">
                      {answer.detectedModule ?? "None"}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs font-medium text-slate-500">
                      Semantic query
                    </p>

                    <p className="mt-1 text-sm font-semibold text-[#0F172A]">
                      {answer.semanticQuery}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs font-medium text-slate-500">
                      Answer mode
                    </p>

                    <div className="mt-2">
                      <Badge variant={answerModeVariant(answer.answerMode)}>
                        {answerModeLabel(answer.answerMode)}
                      </Badge>
                    </div>
                  </div>
                </div>

                <details className="mt-4 rounded-2xl border border-slate-200 p-4">
                  <summary className="cursor-pointer text-sm font-semibold text-[#0F172A]">
                    Pipeline details
                  </summary>

                  <div className="mt-4">
                    <PipelineStats stats={answer.retrievalStats} />
                  </div>
                </details>
              </>
            ) : (
              <div className="mt-4 rounded-2xl bg-slate-50 p-5">
                <p className="text-sm font-semibold text-[#0F172A]">
                  {loading
                    ? "Answer is being generated."
                    : "No answer generated yet."}
                </p>

                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {loading
                    ? "You can move around the workspace while the RAG request continues."
                    : "Run the pipeline to see detected subject, semantic query, answer mode, retrieval stats, verified evidence, and retrieved sources."}
                </p>
              </div>
            )}
          </section>

          {answer ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold text-[#2563EB]">
                Answer snapshot
              </p>

              <div className="mt-4 grid gap-3">
                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-sm font-medium text-slate-600">
                    Claims / topics
                  </p>
                  <p className="text-lg font-semibold text-[#0F172A]">
                    {answer.claims.length}
                  </p>
                </div>

                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-sm font-medium text-slate-600">Sources</p>
                  <p className="text-lg font-semibold text-[#0F172A]">
                    {answer.sources.length}
                  </p>
                </div>

                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-sm font-medium text-slate-600">
                    Kept chunks
                  </p>
                  <p className="text-lg font-semibold text-[#0F172A]">
                    {answer.retrievalStats.keptAfterGrading}
                  </p>
                </div>
              </div>
            </section>
          ) : null}
        </aside>
      </section>
    </AppShell>
  );
}