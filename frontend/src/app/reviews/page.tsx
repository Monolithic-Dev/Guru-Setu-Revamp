"use client";
// SCR-10 Review queue: route stub on fixtures (T1.P3.5). Approve/reject lands in T2.P3.2 (FLOW-05).
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill } from "@/components/ui";
import type { components } from "@/lib/types";

type ReviewItem = components["schemas"]["ReviewItem"];

export default function ReviewsPage() {
  const { data, error, loading, reload } = useApi<ReviewItem[]>("/reviews/certificates", { fixture: fixtures.reviewQueue });

  return (
    <>
      <PageHeader title="Certificate reviews" subtitle="Certificates that need a person to check them." />
      {loading ? (
        <LoadingRegion>
          <Skeleton block />
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : !data || data.length === 0 ? (
        <EmptyState message="Nothing to review right now." />
      ) : (
        <ul className="space-y-3">
          {data.map((item) => (
            <li key={item.certificate.id} className="card flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-black text-gray-900">
                  {item.student.name} · {item.certificate.title}
                </p>
                <p className="text-sm text-gray-600">{item.student.roll_no}</p>
              </div>
              <StatusPill status={item.certificate.status} />
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
