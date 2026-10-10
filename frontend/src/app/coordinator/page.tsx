"use client";
// SCR-11 Coordinator dashboard (FLOW-10, REQ-016, REQ-017, REQ-019). HOD sees names; IQAC sees aggregates only: the
// server omits `needs_attention_list` and `escalated_issues` for IQAC, so those sections simply do not render.
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { AttentionBadge, EmptyState, ErrorState, ExportButton, KpiTile, LoadingRegion, PageHeader, Skeleton, StatusPill } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { formatDate, formatPct } from "@/lib/format";
import type { components } from "@/lib/types";

type Dashboard = components["schemas"]["Dashboard"];

const CATEGORY_LABEL: Record<string, string> = {
  academic: "Academic",
  attendance: "Attendance",
  career: "Career",
  research: "Research",
  personal: "Personal",
  other: "Other",
  confidential: "Confidential",
};

function Bars({ rows, label }: { rows: { name: string; a: number; b?: number }[]; label: string }) {
  const max = Math.max(1, ...rows.map((r) => Math.max(r.a, r.b ?? 0)));
  return (
    <ul className="space-y-2" aria-label={label}>
      {rows.map((r) => (
        <li key={r.name} className="text-sm">
          <div className="flex justify-between font-bold text-gray-800">
            <span>{CATEGORY_LABEL[r.name] ?? r.name}</span>
            <span>{r.b === undefined ? r.a : `${r.b} of ${r.a} resolved`}</span>
          </div>
          <div className="mt-1 h-2.5 rounded-full bg-gray-100" aria-hidden>
            <div className="h-2.5 rounded-full bg-brand/30" style={{ width: `${(r.a / max) * 100}%` }}>
              {r.b !== undefined ? <div className="h-2.5 rounded-full bg-brand" style={{ width: r.a ? `${(r.b / r.a) * 100}%` : 0 }} /> : null}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function CoordinatorPage() {
  const { data, error, loading, reload } = useApi<Dashboard>("/dept/dashboard");

  if (loading) {
    return (
      <>
        <PageHeader title="Department dashboard" />
        <LoadingRegion label="Loading the dashboard">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Skeleton block />
            <Skeleton block />
            <Skeleton block />
            <Skeleton block />
          </div>
        </LoadingRegion>
      </>
    );
  }
  if (error || !data) {
    return (
      <>
        <PageHeader title="Department dashboard" />
        {error ? <ErrorState error={error} onRetry={reload} homeHref="/coordinator" /> : null}
      </>
    );
  }

  const raised = data.issues_by_category.reduce((n, c) => n + c.raised, 0);
  const resolved = data.issues_by_category.reduce((n, c) => n + c.resolved, 0);
  const hod = data.needs_attention_list !== undefined && data.needs_attention_list !== null;
  const noSessions = data.mentors.every((m) => m.meetings_held === 0);

  return (
    <>
      <PageHeader
        title="Department dashboard"
        subtitle={
          <span className="inline-flex items-center gap-2">
            <StatusPill status="draft" /> evidence · {data.term.name}
          </span>
        }
        actions={
          <>
            <ExportButton href="/evidence/mentoring.xlsx" filename={`gurusetu-mentoring-${data.term.id}-DRAFT.xlsx`} label="Export mentoring pack" />
            <ExportButton href="/evidence/achievements.xlsx" filename={`gurusetu-achievements-${data.term.id}-DRAFT.xlsx`} label="Export achievements" />
          </>
        }
      />
      <div className="space-y-8">
        <section aria-label="Key numbers" className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <KpiTile label="Allotted" value={`${data.students_allotted}/${data.students_total}`} sub={`${data.unallotted} unallotted`} />
          <KpiTile label="Mentor : student" value={data.ratio} />
          <KpiTile label="Compliance" value={formatPct(data.compliance_pct)} href="/coordinator/metrics/compliance" highlight={data.compliance_pct < 100} sub="met the minimum meetings" />
          <KpiTile label="Issues" value={`${resolved}/${raised}`} sub="resolved this term" href="/coordinator/metrics/issues_raised" />
          <KpiTile label="Overdue actions" value={data.overdue_actions} href="/coordinator/metrics/overdue_actions" highlight={data.overdue_actions > 0} />
          <KpiTile label="Pending reviews" value={data.pending_reviews} href="/coordinator/metrics/pending_reviews" />
          <KpiTile label="Needs attention" value={data.needs_attention_count ?? 0} href="/coordinator/metrics/needs_attention" highlight={(data.needs_attention_count ?? 0) > 0} sub="students flagged" />
        </section>

        <section aria-labelledby="mentors-title" className="space-y-3">
          <h2 id="mentors-title" className="section-title">
            Mentors
          </h2>
          {noSessions ? <p className="text-sm text-gray-600">No sessions logged this term yet.</p> : null}
          <div className="card overflow-x-auto p-0">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="border-b border-gray-100 text-xs font-black uppercase tracking-wider text-gray-600">
                <tr>
                  <th scope="col" className="px-4 py-3">Mentor</th>
                  <th scope="col" className="px-3 py-3">Mentees</th>
                  <th scope="col" className="px-3 py-3">Meetings</th>
                  <th scope="col" className="px-3 py-3">Compliant</th>
                  <th scope="col" className="px-3 py-3">Issues</th>
                  <th scope="col" className="px-3 py-3">Overdue</th>
                </tr>
              </thead>
              <tbody>
                {data.mentors.map((m) => (
                  <tr key={m.mentor_id} className="border-b border-gray-50 last:border-0">
                    <th scope="row" className="px-4 py-3 font-black text-gray-900">
                      {m.name}
                      {m.overloaded ? <span className="ml-2 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-black text-amber-900">Overloaded</span> : null}
                    </th>
                    <td className="px-3 py-3">{m.mentee_count}</td>
                    <td className="px-3 py-3">{m.meetings_held}</td>
                    <td className={`px-3 py-3 font-bold ${m.compliance_pct < 100 ? "text-brand" : "text-green-800"}`}>
                      {m.mentees_compliant}/{m.mentee_count} · {formatPct(m.compliance_pct)}
                    </td>
                    <td className="px-3 py-3">{m.issues_resolved}/{m.issues_raised}</td>
                    <td className="px-3 py-3">{m.overdue_actions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="grid gap-6 md:grid-cols-2">
          <section aria-labelledby="issues-title" className="card space-y-3">
            <h2 id="issues-title" className="section-title">Issues by category</h2>
            {data.issues_by_category.length === 0 ? (
              <p className="text-sm text-gray-600">No issues this term.</p>
            ) : (
              <Bars label="Issues by category" rows={data.issues_by_category.map((c) => ({ name: c.category, a: c.raised, b: c.resolved }))} />
            )}
          </section>
          <section aria-labelledby="ach-title" className="card space-y-3">
            <h2 id="ach-title" className="section-title">Achievements by type</h2>
            {data.achievements_by_type.length === 0 ? (
              <p className="text-sm text-gray-600">No verified achievements this academic year.</p>
            ) : (
              <Bars label="Achievements by type" rows={data.achievements_by_type.map((t) => ({ name: t.type, a: t.count }))} />
            )}
          </section>
        </div>

        {hod && data.escalated_issues && data.escalated_issues.length > 0 ? (
          <section aria-labelledby="esc-title" className="space-y-3">
            <h2 id="esc-title" className="section-title flex items-center gap-2">
              <AlertTriangle aria-hidden size={16} /> Escalated issues ({data.escalated_issues.length})
            </h2>
            <ul className="space-y-2">
              {data.escalated_issues.map((e) => (
                <li key={e.issue_id} className="card space-y-1 border-amber-200 bg-amber-50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Link href={`/faculty/mentees/${e.student_id}`} className="text-sm font-black text-gray-900 hover:underline">
                      {e.student_name} · {CATEGORY_LABEL[e.category] ?? e.category}
                    </Link>
                    <StatusPill status={e.status} />
                  </div>
                  <p className="text-xs text-gray-700">Raised by {e.mentor_name} on {formatDate(e.raised_at)}</p>
                  <p className="text-sm text-gray-900">{e.text}</p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {hod ? (
          <section aria-labelledby="needs-title" className="space-y-3">
            <h2 id="needs-title" className="section-title">Needs attention ({data.needs_attention_list?.length ?? 0})</h2>
            {data.needs_attention_list && data.needs_attention_list.length > 0 ? (
              <ul className="space-y-2">
                {data.needs_attention_list.map((n) => (
                  <li key={n.student_id} className="card flex flex-wrap items-center justify-between gap-2 p-4">
                    <div>
                      <Link href={`/faculty/mentees/${n.student_id}`} className="text-sm font-black text-gray-900 hover:underline">
                        {n.name}
                      </Link>
                      <p className="text-xs text-gray-600">Mentor: {n.mentor_name}</p>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {n.reasons.map((r) => (
                        <AttentionBadge key={r} reason={r} />
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState message="Nobody needs attention right now." />
            )}
          </section>
        ) : null}
      </div>
    </>
  );
}
