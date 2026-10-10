// Term summary (add-on B2, REQ-032): counts only, from MenteeOverview.term_summary.
import type { components } from "@/lib/types";

type Summary = NonNullable<components["schemas"]["MenteeOverview"]["term_summary"]>;

export function TermSummary({ summary }: { summary: Summary }) {
  const rows: [string, string][] = [
    ["Sessions attended", String(summary.sessions_attended)],
    ["Actions done", `${summary.actions_done} of ${summary.actions_total}`],
    ["Issues raised", String(summary.issues_raised)],
    ["Issues resolved", String(summary.issues_resolved)],
    ["Certificates certified", String(summary.certificates_certified)],
  ];
  return (
    <dl className="grid grid-cols-2 gap-2">
      {rows.map(([k, v]) => (
        <div key={k} className="rounded-xl bg-canvas px-3 py-2">
          <dt className="text-[11px] font-bold uppercase tracking-wider text-gray-600">{k}</dt>
          <dd className="text-lg font-black text-gray-900">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
