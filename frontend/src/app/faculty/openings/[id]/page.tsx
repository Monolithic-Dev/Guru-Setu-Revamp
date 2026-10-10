"use client";
// SCR-09 Candidates: route stub on fixtures (T1.P3.5). Decisions land in T3.P3.3 (FLOW-04).
import { useParams } from "next/navigation";
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill } from "@/components/ui";
import { formatScore } from "@/lib/format";
import type { components } from "@/lib/types";

type Opening = components["schemas"]["Opening"];
type Candidate = components["schemas"]["Candidate"];

export default function CandidatesPage() {
  const { id } = useParams<{ id: string }>();
  const opening = useApi<Opening>(`/openings/${id}`, { fixture: fixtures.opening });
  const cands = useApi<Candidate[]>(`/openings/${id}/candidates`, { fixture: fixtures.candidates });

  return (
    <>
      <PageHeader
        title={opening.data?.title ?? "Opening"}
        subtitle={cands.data ? `${cands.data.length} applicants` : undefined}
        backHref="/faculty/openings"
        backLabel="My openings"
      />
      {cands.loading ? (
        <LoadingRegion>
          <Skeleton block />
        </LoadingRegion>
      ) : cands.error ? (
        <ErrorState error={cands.error} onRetry={cands.reload} homeHref="/faculty/openings" />
      ) : !cands.data || cands.data.length === 0 ? (
        <EmptyState message="No applicants yet." />
      ) : (
        <ol className="space-y-3">
          {cands.data.map((c, i) => (
            <li key={c.application.id} className="card flex flex-wrap items-center justify-between gap-2">
              <p className="font-black text-gray-900">
                {i + 1}. {c.student.name}
              </p>
              <span className="flex items-center gap-2">
                <span className="text-lg font-black text-brand">{formatScore(c.fit.score)}</span>
                <StatusPill status={c.application.status} />
              </span>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
