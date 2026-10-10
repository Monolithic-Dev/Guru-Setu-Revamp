"use client";
// SCR-06 Mentor home: route stub on fixtures (T1.P3.5). Full screen lands in T3.P3.1 (FLOW-09).
import Link from "next/link";
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { AttentionBadge, EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import type { components } from "@/lib/types";

type MenteeRow = components["schemas"]["MenteeRow"];

export default function MentorHomePage() {
  const { data, error, loading, reload } = useApi<MenteeRow[]>("/me/mentees", { fixture: fixtures.mentees });
  const assigned = data?.filter((r) => r.mentorship_type === "assigned") ?? [];

  return (
    <>
      <PageHeader
        title={`My mentees (${assigned.length})`}
        actions={
          <Link href="/faculty/sessions/new" className="btn-primary">
            Log session
          </Link>
        }
      />
      {loading ? (
        <LoadingRegion>
          <Skeleton block />
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : assigned.length === 0 ? (
        <EmptyState message="No mentees assigned yet." />
      ) : (
        <ul className="space-y-3">
          {assigned.map((r) => (
            <li key={r.student_id} className="card flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-black text-gray-900">{r.name}</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {r.attention_reasons.map((reason) => (
                    <AttentionBadge key={reason} reason={reason} />
                  ))}
                </div>
              </div>
              <Link href={`/faculty/mentees/${r.student_id}`} className="btn-secondary">
                Open<span className="sr-only"> {r.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
