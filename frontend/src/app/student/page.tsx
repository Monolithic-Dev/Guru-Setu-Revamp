"use client";
// SCR-02 Student home (FLOW-03, REQ-004, REQ-014, plan section 4.4): recommended openings in groups, each with its
// reasons and eligibility. Eligibility (rules the faculty member wrote down) is shown separately from the fit score,
// and an opening you cannot apply to is never hidden: it sits under "Not eligible yet" with the failing rule.
import Link from "next/link";
import { Briefcase, ChevronRight, GraduationCap, TriangleAlert } from "lucide-react";
import { SkillGapCard } from "@/components/fit/SkillGapCard";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { features } from "@/lib/features";
import { formatDate, formatScore } from "@/lib/format";
import type { components } from "@/lib/types";

type Recommendations = components["schemas"]["Recommendations"];
type Recommended = components["schemas"]["RecommendedOpening"];
type Mentorship = components["schemas"]["MyMentorship"];
type SkillGap = components["schemas"]["SkillGap"];

const VERDICT: Record<string, { label: string; cls: string }> = {
  ready: { label: "Ready", cls: "border-green-200 bg-green-50 text-green-800" },
  close: { label: "Close", cls: "border-amber-200 bg-amber-50 text-amber-900" },
  not_yet: { label: "Not yet", cls: "border-gray-200 bg-gray-100 text-gray-700" },
};
const MODE: Record<string, string> = { on_campus: "On campus", remote: "Remote", hybrid: "Hybrid" };

function MentorshipSummary() {
  const { data, error, loading } = useApi<Mentorship>("/me/mentorship");
  if (loading) return <Skeleton block />;
  if (error || !data) return null; // the full page explains any failure; the home stays usable
  const toConfirm = data.sessions_to_confirm.length;
  return (
    <Link href="/student/mentorship" className="card flex items-center justify-between gap-3 hover:shadow-md">
      <div className="flex items-center gap-3">
        <GraduationCap aria-hidden className="text-brand" size={28} />
        <div>
          <p className="text-sm font-black text-gray-900">
            {data.assigned_mentor ? `My mentor: ${data.assigned_mentor.name}` : "No mentor assigned yet"}
          </p>
          <p className="text-xs font-medium text-gray-600">
            {toConfirm > 0
              ? `${toConfirm} session${toConfirm === 1 ? "" : "s"} to confirm`
              : data.next_followup
                ? `Next follow-up ${formatDate(data.next_followup)}`
                : data.assigned_mentor
                  ? "Nothing to do right now"
                  : "Your HOD allots mentors."}
          </p>
        </div>
      </div>
      <ChevronRight aria-hidden size={18} className="text-gray-500" />
    </Link>
  );
}

function OpeningCard({ opening }: { opening: Recommended }) {
  const verdict = VERDICT[opening.my_fit.verdict];
  const problems = opening.eligibility.checks.filter((c) => c.status === "failed");
  const unknown = opening.eligibility.checks.filter((c) => c.status === "unknown");
  return (
    <li className="card space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link href={`/student/openings/${opening.id}`} className="text-base font-black text-gray-900 hover:underline">
            {opening.title}
          </Link>
          <p className="text-xs font-medium text-gray-600">
            <Link href={`/faculty-profile/${opening.faculty.user_id}`} className="underline">
              {opening.faculty.name}
            </Link>
            {opening.mode ? ` · ${MODE[opening.mode] ?? opening.mode}` : ""}
            {opening.duration_weeks ? ` · ${opening.duration_weeks} weeks` : ""}
            {opening.hours_per_week ? ` · ${opening.hours_per_week} h/week` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {opening.my_application_status ? <StatusPill status={opening.my_application_status} /> : null}
          <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-black ${verdict.cls}`}>
            <span className="text-sm">{formatScore(opening.my_fit.score)}</span> {verdict.label}
          </span>
        </div>
      </div>
      <ul className="flex flex-wrap gap-1.5" aria-label="Required skills">
        {opening.required_skills.map((s) => (
          <li key={s} className="rounded-full border border-gray-200 bg-gray-50 px-2.5 py-0.5 text-xs font-bold text-gray-700">
            {s}
          </li>
        ))}
      </ul>
      {opening.reasons.length > 0 ? (
        <ul className="list-inside list-disc text-sm text-gray-700">
          {opening.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      ) : null}
      <p className="text-xs font-medium text-gray-600">
        {opening.positions_left} of {opening.positions} position{opening.positions === 1 ? "" : "s"} left
        {opening.deadline ? ` · apply by ${formatDate(opening.deadline)}` : ""}
        {opening.min_cgpa != null ? ` · CGPA ${opening.min_cgpa} or more` : ""}
        {opening.eligible_years?.length ? ` · year ${opening.eligible_years.join(", ")}` : ""}
      </p>
      {problems.length > 0 ? (
        <div role="note" className="flex gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <TriangleAlert aria-hidden size={18} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-black">{opening.eligibility.mode === "strict" ? "You can't apply yet" : "Heads up, you can still apply"}</p>
            <ul className="list-inside list-disc">
              {problems.map((c) => (
                <li key={c.rule}>{c.detail}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : unknown.length > 0 ? (
        <p className="text-xs font-medium text-gray-600">{unknown.map((c) => c.detail).join(" ")}</p>
      ) : null}
    </li>
  );
}

export default function StudentHomePage() {
  const { data, error, loading, reload } = useApi<Recommendations>("/me/recommendations");
  const gaps = useApi<SkillGap[]>(features.skillGap ? "/me/skill-gaps" : null);
  const total = data?.groups.reduce((n, g) => n + g.items.length, 0) ?? 0;

  return (
    <>
      <PageHeader title="Home" subtitle="Research openings recommended for you, and why" />
      <div className="space-y-6">
        <MentorshipSummary />
        {data && data.completeness_percent < 100 ? (
          <Link href="/student/profile" className="card flex items-center justify-between gap-3 hover:shadow-md">
            <div>
              <p className="text-sm font-black text-gray-900">Your profile is {data.completeness_percent}% complete</p>
              <p className="text-xs font-medium text-gray-600">
                {data.cold_start
                  ? "Add at least two skills and your interests so we can recommend better."
                  : "A fuller profile gives better recommendations."}
              </p>
            </div>
            <ChevronRight aria-hidden size={18} className="text-gray-500" />
          </Link>
        ) : null}
        {features.skillGap ? <SkillGapCard gaps={gaps.data} loading={gaps.loading} /> : null}
        {loading ? (
          <LoadingRegion label="Loading openings">
            <div className="space-y-3">
              <Skeleton block />
              <Skeleton block />
            </div>
          </LoadingRegion>
        ) : error ? (
          <ErrorState error={error} onRetry={reload} homeHref="/student" />
        ) : total === 0 ? (
          <EmptyState icon={<Briefcase size={36} />} message="No open openings right now." />
        ) : (
          data?.groups.map((group) => (
            <section key={group.key} aria-labelledby={`group-${group.key}`} className="space-y-3">
              {group.key === "stretch" ? (
                <details>
                  <summary id={`group-${group.key}`} className="section-title cursor-pointer">
                    {group.label} ({group.items.length})
                  </summary>
                  <ul className="mt-3 space-y-3">
                    {group.items.map((o) => (
                      <OpeningCard key={o.id} opening={o} />
                    ))}
                  </ul>
                </details>
              ) : (
                <>
                  <h2 id={`group-${group.key}`} className="section-title">
                    {group.label} ({group.items.length})
                  </h2>
                  <ul className="space-y-3">
                    {group.items.map((o) => (
                      <OpeningCard key={o.id} opening={o} />
                    ))}
                  </ul>
                </>
              )}
            </section>
          ))
        )}
      </div>
    </>
  );
}
