"use client";
// SCR-16 Faculty track record (REQ-035, API-044): facts only. There is no rating, review or score on this page.
import { useParams } from "next/navigation";
import { ErrorState, KpiTile, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import type { components } from "@/lib/types";

type TrackRecord = components["schemas"]["TrackRecord"];

export default function FacultyProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, loading, reload } = useApi<TrackRecord>(`/faculty/${id}/track-record`);

  return (
    <>
      <PageHeader title={data?.name ?? "Faculty"} subtitle="Facts about posted openings and decisions. Not a rating." backHref="/student" backLabel="Home" />
      {loading ? (
        <LoadingRegion label="Loading the track record">
          <Skeleton block />
        </LoadingRegion>
      ) : error || !data ? (
        error ? <ErrorState error={error} onRetry={reload} homeHref="/student" /> : null
      ) : (
        <section aria-label="Track record" className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <KpiTile label="Openings posted" value={data.openings_posted} />
          <KpiTile label="Guide links accepted" value={data.guide_links_accepted} />
          <KpiTile label="Guide links completed" value={data.guide_links_completed} />
          <KpiTile
            label="Median days to first decision"
            value={data.median_days_to_first_decision == null ? "—" : data.median_days_to_first_decision.toFixed(1)}
            sub={data.median_days_to_first_decision == null ? "No decisions yet" : undefined}
          />
        </section>
      )}
    </>
  );
}
