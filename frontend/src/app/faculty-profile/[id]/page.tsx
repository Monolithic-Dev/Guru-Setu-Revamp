"use client";
// SCR-16 Faculty page (REQ-035, API-053): the profile a faculty member wrote plus the track record. Facts only:
// there is no rating, review or score on this page.
import Link from "next/link";
import { useParams } from "next/navigation";
import { ErrorState, KpiTile, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import type { components } from "@/lib/types";

type FacultyPublic = components["schemas"]["FacultyPublic"];

export default function FacultyProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, loading, reload } = useApi<FacultyPublic>(`/faculty/${id}`);
  const p = data?.profile;
  const t = data?.track_record;

  return (
    <>
      <PageHeader
        title={p?.name ?? "Faculty"}
        subtitle={p ? `${p.designation} · ${p.dept_code}` : "Facts about posted openings and decisions. Not a rating."}
        backHref="/student"
        backLabel="Home"
      />
      {loading ? (
        <LoadingRegion label="Loading the faculty page">
          <Skeleton block />
        </LoadingRegion>
      ) : error || !data || !p || !t ? (
        error ? <ErrorState error={error} onRetry={reload} homeHref="/student" /> : null
      ) : (
        <div className="space-y-6">
          <section aria-label="Track record" className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile label="Openings posted" value={t.openings_posted} />
            <KpiTile label="Guide links accepted" value={t.guide_links_accepted} />
            <KpiTile label="Guide links completed" value={t.guide_links_completed} />
            <KpiTile
              label="Median days to first decision"
              value={t.median_days_to_first_decision == null ? "—" : t.median_days_to_first_decision.toFixed(1)}
              sub={t.median_days_to_first_decision == null ? "No decisions yet" : undefined}
            />
          </section>

          <section aria-labelledby="areas-title" className="card space-y-3">
            <h2 id="areas-title" className="section-title">Research and expertise</h2>
            {p.research_areas.length === 0 && p.expertise.length === 0 ? (
              <p className="text-sm text-gray-600">Nothing listed yet.</p>
            ) : (
              <>
                <ul className="flex flex-wrap gap-1.5" aria-label="Research areas">
                  {p.research_areas.map((a) => (
                    <li key={a.concept} className="rounded-full border border-brand-line bg-brand-soft px-2.5 py-0.5 text-xs font-black text-brand">
                      {a.concept}{a.primary ? " · primary" : ""}
                    </li>
                  ))}
                </ul>
                {p.expertise.length > 0 ? (
                  <ul className="flex flex-wrap gap-1.5" aria-label="Expertise">
                    {p.expertise.map((x) => (
                      <li key={x} className="rounded-full border border-gray-200 bg-gray-50 px-2.5 py-0.5 text-xs font-bold text-gray-700">{x}</li>
                    ))}
                  </ul>
                ) : null}
              </>
            )}
          </section>

          {p.courses.length > 0 ? (
            <section aria-labelledby="courses-title" className="card space-y-2">
              <h2 id="courses-title" className="section-title">Subjects taught</h2>
              <ul className="space-y-1 text-sm text-gray-800">
                {p.courses.map((c) => (
                  <li key={c.code}>
                    <strong>{c.code}</strong> {c.title}
                    {c.term_id ? <span className="text-gray-600"> · {c.term_id}</span> : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section aria-labelledby="about-title" className="card space-y-2 text-sm text-gray-800">
            <h2 id="about-title" className="section-title">About</h2>
            {p.qualifications.length > 0 ? (
              <p>
                <strong>Qualifications (self-reported):</strong>{" "}
                {p.qualifications.map((q) => `${q.degree}, ${q.institution}${q.year ? ` (${q.year})` : ""}`).join("; ")}
              </p>
            ) : null}
            {p.office_hours ? <p><strong>Office hours:</strong> {p.office_hours}</p> : null}
            <p>
              <strong>Guiding:</strong> {p.guided_students ?? 0}
              {p.max_guided_students != null ? ` of ${p.max_guided_students}` : ""} student{p.guided_students === 1 ? "" : "s"} ·{" "}
              {p.accepting_guides ? "taking new students" : "not taking new students"}
            </p>
            {p.publications.length > 0 ? (
              <div>
                <strong>Selected publications (self-listed):</strong>
                <ul className="list-inside list-disc">
                  {p.publications.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {p.links.length > 0 ? (
              <p>
                <strong>Links:</strong>{" "}
                {p.links.map((l) => (
                  <a key={l} href={l} target="_blank" rel="noopener noreferrer" className="mr-2 text-brand underline">{l}</a>
                ))}
              </p>
            ) : null}
          </section>

          {data.open_openings && data.open_openings.length > 0 ? (
            <section aria-labelledby="open-title" className="card space-y-2">
              <h2 id="open-title" className="section-title">Open openings</h2>
              <ul className="space-y-1">
                {data.open_openings.map((o) => (
                  <li key={o.id}>
                    <Link href={`/student/openings/${o.id}`} className="text-sm font-bold text-gray-900 underline">{o.title}</Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      )}
    </>
  );
}
