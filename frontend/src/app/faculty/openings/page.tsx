"use client";
// SCR-15 My openings (REQ-005, REQ-030): the faculty member's own openings with applicant counts, and (A9) a create form.
import Link from "next/link";
import { useEffect, useState } from "react";
import { Briefcase, Plus } from "lucide-react";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { features } from "@/lib/features";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

type Opening = components["schemas"]["OpeningSummary"];

export default function MyOpeningsPage() {
  const { data, error, loading, reload } = useApi<Opening[]>("/openings");
  const [me, setMe] = useState<string | null>(null);
  useEffect(() => setMe(getSession()?.userId ?? null), []);
  const mine = (data ?? []).filter((o) => o.faculty.user_id === me);

  return (
    <>
      <PageHeader
        title={`My openings${data ? ` (${mine.length})` : ""}`}
        actions={
          features.createOpening ? (
            <Link href="/faculty/openings/new" className="btn-primary">
              <Plus aria-hidden size={16} /> New opening
            </Link>
          ) : undefined
        }
      />
      {loading ? (
        <LoadingRegion label="Loading openings">
          <Skeleton block />
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={reload} homeHref="/faculty" />
      ) : mine.length === 0 ? (
        <EmptyState icon={<Briefcase size={36} />} message="You haven't posted an opening yet." />
      ) : (
        <ul className="space-y-3">
          {mine.map((o) => (
            <li key={o.id}>
              <Link href={`/faculty/openings/${o.id}`} className="card block hover:shadow-md">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h2 className="text-base font-black text-gray-900">{o.title}</h2>
                  <StatusPill status={o.status === "open" ? "open" : "completed"} />
                </div>
                <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Required skills">
                  {o.required_skills.map((s) => (
                    <li key={s} className="rounded-full border border-gray-200 bg-gray-50 px-2.5 py-0.5 text-xs font-bold text-gray-700">
                      {s}
                    </li>
                  ))}
                </ul>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
