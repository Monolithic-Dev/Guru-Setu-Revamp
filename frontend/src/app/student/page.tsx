"use client";
// SCR-02 Student home (FLOW-03, REQ-004, REQ-014): mentorship summary on top, then open openings with my fit.
import Link from "next/link";
import { Briefcase, ChevronRight, GraduationCap } from "lucide-react";
import { SkillGapCard } from "@/components/fit/SkillGapCard";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { features } from "@/lib/features";
import { formatDate, formatScore } from "@/lib/format";
import type { components } from "@/lib/types";

type Opening = components["schemas"]["OpeningSummary"];
type Mentorship = components["schemas"]["MyMentorship"];
type SkillGap = components["schemas"]["SkillGap"];

const VERDICT: Record<string, { label: string; cls: string }> = {
  ready: { label: "Ready", cls: "border-green-200 bg-green-50 text-green-800" },
  close: { label: "Close", cls: "border-amber-200 bg-amber-50 text-amber-900" },
  not_yet: { label: "Not yet", cls: "border-gray-200 bg-gray-100 text-gray-700" },
};

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

function OpeningCard({ opening }: { opening: Opening }) {
  const fit = opening.my_fit;
  const verdict = fit ? VERDICT[fit.verdict] : undefined;
  return (
    <li>
      <Link href={`/student/openings/${opening.id}`} className="card block hover:shadow-md">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-base font-black text-gray-900">{opening.title}</h3>
            <p className="text-xs font-medium text-gray-600">{opening.faculty.name}</p>
          </div>
          <div className="flex items-center gap-2">
            {opening.my_application_status ? <StatusPill status={opening.my_application_status} /> : null}
            {fit && verdict ? (
              <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-black ${verdict.cls}`}>
                <span className="text-sm">{formatScore(fit.score)}</span> {verdict.label}
              </span>
            ) : null}
          </div>
        </div>
        <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Required skills">
          {opening.required_skills.map((s) => (
            <li key={s} className="rounded-full border border-gray-200 bg-gray-50 px-2.5 py-0.5 text-xs font-bold text-gray-700">
              {s}
            </li>
          ))}
        </ul>
      </Link>
    </li>
  );
}

export default function StudentHomePage() {
  const { data, error, loading, reload } = useApi<Opening[]>("/openings");
  const gaps = useApi<SkillGap[]>(features.skillGap ? "/me/skill-gaps" : null);
  const openings = (data ?? []).filter((o) => o.status === "open");

  return (
    <>
      <PageHeader title="Home" subtitle="Research openings and how well you fit them" />
      <div className="space-y-6">
        <MentorshipSummary />
        {features.skillGap ? <SkillGapCard gaps={gaps.data} loading={gaps.loading} /> : null}
        <section aria-labelledby="openings-title" className="space-y-3">
          <h2 id="openings-title" className="section-title">
            Openings
          </h2>
          {loading ? (
            <LoadingRegion label="Loading openings">
              <div className="space-y-3">
                <Skeleton block />
                <Skeleton block />
              </div>
            </LoadingRegion>
          ) : error ? (
            <ErrorState error={error} onRetry={reload} homeHref="/student" />
          ) : openings.length === 0 ? (
            <EmptyState icon={<Briefcase size={36} />} message="No open openings right now." />
          ) : (
            <ul className="space-y-3">
              {[...openings]
                .sort((a, b) => (b.my_fit?.score ?? -1) - (a.my_fit?.score ?? -1) || a.title.localeCompare(b.title))
                .map((o) => (
                  <OpeningCard key={o.id} opening={o} />
                ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
