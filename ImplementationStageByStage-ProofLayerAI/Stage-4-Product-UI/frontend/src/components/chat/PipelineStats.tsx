import type { RetrievalStats } from "@/types/rag";

type PipelineStatsProps = {
  stats: RetrievalStats;
};

const statItems = [
  {
    key: "candidates",
    label: "Candidates",
    description: "Initial chunks retrieved from the vector store.",
  },
  {
    key: "reranked",
    label: "Re-ranked",
    description: "Chunks reordered by local relevance scoring.",
  },
  {
    key: "keptAfterGrading",
    label: "Kept after grading",
    description: "Final chunks that passed relevance checks.",
  },
] as const;

export function PipelineStats({ stats }: PipelineStatsProps) {
  return (
    <div className="grid gap-3">
      {statItems.map((item) => (
        <div
          key={item.key}
          className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-[#0F172A]">
                {item.label}
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-600">
                {item.description}
              </p>
            </div>

            <p className="shrink-0 text-3xl font-semibold tracking-tight text-[#0F172A]">
              {stats[item.key]}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
