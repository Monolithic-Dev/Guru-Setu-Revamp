"use client";
// SCR-19 Find a guide (plan section 4.5): faculty in your department ordered by the topics they share with you.
// Deliberately no score and no rank number: it is a per-student ordering shown as shared-topic chips, never a
// leaderboard of faculty (NG-11).
import Link from "next/link";
import { useState } from "react";
import { Compass } from "lucide-react";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import type { components } from "@/lib/types";

type Card = components["schemas"]["FacultyCard"];

export default function FindAGuidePage() {
  const [query, setQuery] = useState("");
  const [accepting, setAccepting] = useState(false);
  const params = new URLSearchParams();
  if (query.trim()) params.set("query", query.trim());
  if (accepting) params.set("accepting", "true");
  const path = `/faculty${params.toString() ? `?${params}` : ""}`;
  const { data, error, loading, reload } = useApi<Card[]>(path);

  return (
    <>
      <PageHeader title="Find a guide" subtitle="Faculty ordered by the topics they share with your profile" />
      <div className="space-y-4">
        <div className="card flex flex-wrap items-end gap-4">
          <div className="min-w-[220px] flex-1">
            <label htmlFor="guide-query" className="label">Search by name or topic</label>
            <input id="guide-query" className="input" value={query} maxLength={60} onChange={(e) => setQuery(e.target.value)} />
          </div>
          <label className="flex min-h-[44px] items-center gap-2 text-sm font-bold text-gray-900">
            <input type="checkbox" className="h-5 w-5 accent-[#8c1515]" checked={accepting} onChange={(e) => setAccepting(e.target.checked)} />
            Only faculty taking new students
          </label>
        </div>
        {loading ? (
          <LoadingRegion label="Loading faculty">
            <Skeleton block />
          </LoadingRegion>
        ) : error ? (
          <ErrorState error={error} onRetry={reload} homeHref="/student" />
        ) : !data || data.length === 0 ? (
          <EmptyState icon={<Compass size={36} />} message="No faculty match that search." />
        ) : (
          <ul className="space-y-3">
            {data.map((f) => (
              <li key={f.user_id} className="card space-y-2">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <Link href={`/faculty-profile/${f.user_id}`} className="text-base font-black text-gray-900 hover:underline">{f.name}</Link>
                    <p className="text-xs font-medium text-gray-600">{f.designation}</p>
                  </div>
                  <p className="text-xs font-bold text-gray-700">
                    {f.accepting_guides ? "Taking new students" : "Not taking new students"} · {f.open_openings} open opening{f.open_openings === 1 ? "" : "s"}
                    {f.max_guided_students != null ? ` · guiding ${f.guided_students ?? 0} of ${f.max_guided_students}` : ""}
                  </p>
                </div>
                {f.shared_topics.length > 0 ? (
                  <div>
                    <p className="text-xs font-black uppercase tracking-widest text-gray-600">You share</p>
                    <ul className="mt-1 flex flex-wrap gap-1.5" aria-label={`Topics you share with ${f.name}`}>
                      {f.shared_topics.map((t) => (
                        <li key={t} className="rounded-full border border-green-200 bg-green-50 px-2.5 py-0.5 text-xs font-bold text-green-900">{t}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-xs text-gray-600">No shared topics yet. Add skills and interests to your profile to improve this.</p>
                )}
                {f.research_areas.length > 0 ? (
                  <p className="text-xs text-gray-600">Research: {f.research_areas.join(", ")}</p>
                ) : (
                  <p className="text-xs text-gray-600">No research areas listed.</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
