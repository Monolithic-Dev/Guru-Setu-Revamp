"use client";
// SCR-07 Mentee 360: route stub on fixtures (T1.P3.5). Full screen lands in T3.P3.2 (REQ-013).
import { useParams } from "next/navigation";
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { ErrorState, LoadingRegion, PageHeader, Skeleton, TrustBadge } from "@/components/ui";
import type { components } from "@/lib/types";

type MenteeOverview = components["schemas"]["MenteeOverview"];

export default function MenteeOverviewPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const { data, error, loading, reload } = useApi<MenteeOverview>(`/mentees/${studentId}/overview`, {
    fixture: fixtures.menteeOverview,
  });

  if (loading) {
    return (
      <LoadingRegion>
        <Skeleton block />
      </LoadingRegion>
    );
  }
  if (error || !data) return error ? <ErrorState error={error} onRetry={reload} homeHref="/faculty" /> : null;

  return (
    <>
      <PageHeader
        title={data.student.name}
        subtitle={`${data.student.roll_no} · Year ${data.student.year}`}
        backHref="/faculty"
        backLabel="My mentees"
      />
      <section className="card space-y-2">
        <h2 className="section-title">Skills</h2>
        <div className="flex flex-wrap gap-2">
          {data.student.skills.map((s) => (
            <span key={s.concept} className="inline-flex items-center gap-1.5 text-sm font-bold">
              {s.concept} <TrustBadge level={s.trust_level} />
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
