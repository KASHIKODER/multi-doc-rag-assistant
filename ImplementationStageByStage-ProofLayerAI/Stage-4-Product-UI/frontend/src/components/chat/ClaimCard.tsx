import type { VerifiedClaim } from "@/types/rag";
import { Badge } from "@/components/ui/Badge";

type ClaimCardProps = {
  claim: VerifiedClaim;
  index: number;
};

function confidenceVariant(confidence: VerifiedClaim["confidence"]) {
  if (confidence === "high") return "success";
  if (confidence === "medium") return "primary";
  return "muted";
}

export function ClaimCard({ claim, index }: ClaimCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 p-4">
      <div className="flex gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#10B981]/10 text-sm font-semibold text-[#10B981]">
          {index + 1}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <p className="text-sm font-semibold leading-6 text-[#0F172A]">
              {claim.claim}
            </p>

            <Badge variant={confidenceVariant(claim.confidence)}>
              {claim.confidence}
            </Badge>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="outline">{claim.source}</Badge>
            <Badge variant="outline">page {claim.page}</Badge>

            {claim.subject ? (
              <Badge variant="primary">{claim.subject}</Badge>
            ) : null}

            {claim.module ? (
              <Badge variant="neutral">module {claim.module}</Badge>
            ) : null}
          </div>

          {claim.title ? (
            <p className="mt-3 text-xs leading-5 text-slate-500">
              Title: {claim.title}
            </p>
          ) : null}
        </div>
      </div>
    </article>
  );
}
