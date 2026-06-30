import type { RagAnswer } from "@/types/rag";
import { Badge } from "@/components/ui/Badge";
import { ClaimCard } from "@/components/chat/ClaimCard";

type AnswerCardProps = {
  answer: RagAnswer;
};

function answerModeLabel(mode: RagAnswer["answerMode"]) {
  if (mode === "citation") return "Citation-backed answer";
  if (mode === "topic") return "Document-grounded topic answer";
  return "Unsupported question";
}

function answerModeVariant(mode: RagAnswer["answerMode"]) {
  if (mode === "citation") return "success";
  if (mode === "topic") return "primary";
  return "muted";
}

function answerTitle(answer: RagAnswer) {
  if (answer.detectedSubject) {
    return `${answer.detectedSubject} answer`;
  }

  if (answer.answerMode === "unsupported") {
    return "Unsupported question";
  }

  return "Document answer";
}

function evidenceSectionTitle(mode: RagAnswer["answerMode"]) {
  if (mode === "topic") return "Topics / Concepts Found";
  if (mode === "citation") return "Verified claims";
  return "Evidence";
}

function evidenceCountLabel(answer: RagAnswer) {
  const count = answer.claims.length;

  if (answer.answerMode === "topic") {
    return `${count} ${count === 1 ? "topic" : "topics"}`;
  }

  if (answer.answerMode === "citation") {
    return `${count} ${count === 1 ? "claim" : "claims"}`;
  }

  return `${count} items`;
}

function emptyEvidenceMessage(mode: RagAnswer["answerMode"]) {
  if (mode === "topic") {
    return "No document-grounded topics were found for this answer.";
  }

  if (mode === "citation") {
    return "No verified claims were found for this answer.";
  }

  return "No supported evidence was found for this question.";
}

export function AnswerCard({ answer }: AnswerCardProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold text-[#2563EB]">
            Source-grounded answer
          </p>

          <h2 className="mt-2 text-xl font-semibold text-[#0F172A]">
            {answerTitle(answer)}
          </h2>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant={answerModeVariant(answer.answerMode)}>
            {answerModeLabel(answer.answerMode)}
          </Badge>

          {answer.detectedSubject ? (
            <Badge variant="primary">{answer.detectedSubject}</Badge>
          ) : null}
        </div>
      </div>

      <div className="mt-5 rounded-2xl bg-slate-50 p-5">
        <p className="text-xs font-medium text-slate-500">Summary</p>

        <p className="mt-2 text-sm leading-7 text-slate-700">
          {answer.summary}
        </p>
      </div>

      <div className="mt-6">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-sm font-semibold text-[#0F172A]">
            {evidenceSectionTitle(answer.answerMode)}
          </h3>

          <Badge variant="outline">{evidenceCountLabel(answer)}</Badge>
        </div>

        {answer.claims.length > 0 ? (
          <div className="mt-4 grid gap-4">
            {answer.claims.map((claim, index) => (
              <ClaimCard key={claim.id} claim={claim} index={index} />
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-600">
              {emptyEvidenceMessage(answer.answerMode)}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
