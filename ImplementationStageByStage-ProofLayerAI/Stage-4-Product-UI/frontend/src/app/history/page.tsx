"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { APP_ROUTES } from "@/lib/constants";
import {
  clearChatHistory,
  formatHistoryDate,
  getChatHistory,
  getChatHistoryStats,
} from "@/lib/chat-history";
import type { ChatHistoryItem, ChatHistoryStats } from "@/types/history";

function answerModeLabel(mode: ChatHistoryItem["answerMode"]) {
  if (mode === "citation") return "Citation-backed";
  if (mode === "topic") return "Topic answer";
  return "Unsupported";
}

function answerModeVariant(mode: ChatHistoryItem["answerMode"]) {
  if (mode === "citation") return "success";
  if (mode === "topic") return "primary";
  return "muted";
}

const emptyStats: ChatHistoryStats = {
  total: 0,
  citationAnswers: 0,
  topicAnswers: 0,
  unsupportedAnswers: 0,
};

export default function HistoryPage() {
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [stats, setStats] = useState<ChatHistoryStats>(emptyStats);
  const [loaded, setLoaded] = useState(false);

  function loadHistory() {
    const items = getChatHistory();
    setHistory(items);
    setStats(getChatHistoryStats(items));
    setLoaded(true);
  }

  function handleClearHistory() {
    clearChatHistory();
    setHistory([]);
    setStats(emptyStats);
  }

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <AppShell activePath={APP_ROUTES.history} title="History">
      <PageHeader
        title="History"
        description="Review questions saved from the Ask page. This MVP stores history locally in your browser and can later be migrated to PostgreSQL."
        action={
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" onClick={loadHistory}>
              Refresh
            </Button>

            <Link
              href={APP_ROUTES.ask}
              className="rounded-xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
            >
              Ask New Question
            </Link>
          </div>
        }
      />

      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Total saved</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {stats.total}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Questions saved from the Ask workspace.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Citations</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {stats.citationAnswers}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Claim-level citation-backed answers.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Topics</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {stats.topicAnswers}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Metadata-grounded topic answers.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Unsupported</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {stats.unsupportedAnswers}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Questions without enough support.
          </p>
        </div>
      </section>

      {history.length > 0 ? (
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#2563EB]">
                Saved questions
              </p>

              <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
                Local browser history
              </h2>

              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
                This history is stored in localStorage for the current browser.
                Later, it can be moved to a user-specific database table.
              </p>
            </div>

            <Button variant="secondary" onClick={handleClearHistory}>
              Clear History
            </Button>
          </div>

          <div className="mt-6 grid gap-4">
            {history.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-slate-200 p-5"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {formatHistoryDate(item.createdAt)}
                    </p>

                    <h3 className="mt-2 text-lg font-semibold text-[#0F172A]">
                      {item.question}
                    </h3>

                    <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
                      {item.summary}
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {item.detectedSubject ? (
                        <Badge variant="primary">{item.detectedSubject}</Badge>
                      ) : (
                        <Badge variant="muted">No subject</Badge>
                      )}

                      <Badge variant={answerModeVariant(item.answerMode)}>
                        {answerModeLabel(item.answerMode)}
                      </Badge>

                      <Badge variant="outline">
                        {item.claimCount}{" "}
                        {item.answerMode === "topic" ? "topics" : "claims"}
                      </Badge>

                      <Badge variant="outline">
                        {item.sourceCount} sources
                      </Badge>
                    </div>
                  </div>

                  <Link
                    href={APP_ROUTES.ask}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-[#0F172A] transition hover:border-[#2563EB]"
                  >
                    Ask Again
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : (
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-[#2563EB]">No history yet</p>

          <h2 className="mt-2 text-2xl font-semibold text-[#0F172A]">
            Run your first document question.
          </h2>

          <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600">
            Once you ask a question and receive an answer, it will appear here
            with subject, answer mode, claim/topic count, source count, and
            timestamp.
          </p>

          <div className="mt-6">
            <Link
              href={APP_ROUTES.ask}
              className="rounded-xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
            >
              Go to Ask Page
            </Link>
          </div>

          {!loaded ? (
            <p className="mt-4 text-xs text-slate-500">Loading history...</p>
          ) : null}
        </section>
      )}
    </AppShell>
  );
}