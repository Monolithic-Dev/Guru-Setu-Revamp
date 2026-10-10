"use client";
// SCR-08 Log a session: route stub on fixtures (T1.P3.5). The form lands in T2.P3.3 (FLOW-07).
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { ErrorState, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import type { components } from "@/lib/types";

type MenteeRow = components["schemas"]["MenteeRow"];

export default function NewSessionPage() {
  const { data, error, loading, reload } = useApi<MenteeRow[]>("/me/mentees", { fixture: fixtures.mentees });

  return (
    <>
      <PageHeader title="Log a session" backHref="/faculty" backLabel="My mentees" />
      {loading ? (
        <LoadingRegion>
          <Skeleton block />
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : (
        <div className="card">
          <p className="section-title mb-2">Attendees</p>
          <p className="text-sm text-gray-700">
            {data?.filter((r) => r.mentorship_type === "assigned").length ?? 0} assigned mentees available.
          </p>
        </div>
      )}
    </>
  );
}
