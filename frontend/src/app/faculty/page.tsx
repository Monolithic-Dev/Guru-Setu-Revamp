"use client";
// SCR-06 Mentor home (FLOW-09, REQ-012): assigned mentees (flagged first, with reasons), then guided students.
import Link from "next/link";
import { BellRing, Plus, Users } from "lucide-react";
import { MenteeRow } from "@/components/mentor/MenteeRow";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { features } from "@/lib/features";
import type { components } from "@/lib/types";

type Row = components["schemas"]["MenteeRow"];
type Reminder = components["schemas"]["Reminder"];

/** Flagged first, then by number of reasons, then by name (backend §6.4); the server already sorts, this keeps it stable. */
function sortRows(rows: Row[]): Row[] {
  return [...rows].sort(
    (a, b) =>
      Number(b.needs_attention) - Number(a.needs_attention) ||
      b.attention_reasons.length - a.attention_reasons.length ||
      a.name.localeCompare(b.name),
  );
}

function RemindersLink() {
  const { data } = useApi<Reminder[]>("/me/reminders");
  if (!data || data.length === 0) return null;
  return (
    <Link href="/notifications" className="btn-ghost border border-gold-line bg-gold-soft text-gold-ink">
      <BellRing aria-hidden size={16} />
      {data.length} reminder{data.length === 1 ? "" : "s"}
    </Link>
  );
}

export default function MentorHomePage() {
  const { data, error, loading, reload } = useApi<Row[]>("/me/mentees");
  const assigned = sortRows((data ?? []).filter((r) => r.mentorship_type === "assigned"));
  const guided = sortRows((data ?? []).filter((r) => r.mentorship_type === "guide"));
  const flagged = assigned.filter((r) => r.needs_attention).length;

  return (
    <>
      <PageHeader
        title={`My mentees (${assigned.length})`}
        subtitle={data ? (flagged > 0 ? `${flagged} need${flagged === 1 ? "s" : ""} attention` : "Everyone is on track") : undefined}
        actions={
          <>
            {features.reminders ? <RemindersLink /> : null}
            <Link href="/faculty/sessions/new" className="btn-primary">
              <Plus aria-hidden size={16} /> Log session
            </Link>
          </>
        }
      />
      {loading ? (
        <LoadingRegion label="Loading mentees">
          <div className="space-y-3">
            <Skeleton block />
            <Skeleton block />
            <Skeleton block />
          </div>
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : assigned.length === 0 && guided.length === 0 ? (
        <EmptyState icon={<Users size={36} />} message="No mentees assigned yet." />
      ) : (
        <div className="space-y-8">
          <section aria-labelledby="assigned-title" className="space-y-3">
            <h2 id="assigned-title" className="section-title">
              Assigned mentees
            </h2>
            {assigned.length === 0 ? (
              <p className="text-sm text-gray-600">No mentees assigned yet.</p>
            ) : (
              <ul className="space-y-3">
                {assigned.map((r) => (
                  <MenteeRow key={`a-${r.student_id}`} row={r} />
                ))}
              </ul>
            )}
          </section>
          {guided.length > 0 ? (
            <section aria-labelledby="guided-title" className="space-y-3">
              <h2 id="guided-title" className="section-title">
                Guided students ({guided.length})
              </h2>
              <ul className="space-y-3">
                {guided.map((r) => (
                  <MenteeRow key={`g-${r.student_id}`} row={r} />
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      )}
    </>
  );
}
