import type { RetrievedSource } from "@/types/rag";
import { Badge } from "@/components/ui/Badge";

type SourceCardProps = {
  source: RetrievedSource;
};

export function SourceCard({ source }: SourceCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold text-[#0F172A]">
            {source.fileName}
          </p>

          {source.title ? (
            <p className="mt-1 text-xs text-slate-500">{source.title}</p>
          ) : null}
        </div>

        <Badge variant="outline">page {source.page}</Badge>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {source.subject ? <Badge variant="primary">{source.subject}</Badge> : null}

        {source.module ? (
          <Badge variant="neutral">module {source.module}</Badge>
        ) : null}
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-600">
        {source.preview}
      </p>
    </article>
  );
}
