// One mentee on the mentor home (FLOW-09, REQ-012). Every count is written as text; flagged rows show reasons.
import Link from "next/link";
import { AlertTriangle, CalendarClock, ClipboardList, MessageSquareWarning } from "lucide-react";
import { AttentionBadge, Avatar } from "@/components/ui";
import { formatRelative } from "@/lib/format";
import type { components } from "@/lib/types";

type Row = components["schemas"]["MenteeRow"];

function Stat({ icon, text, warn = false }: { icon: React.ReactNode; text: string; warn?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-bold ${warn ? "text-red-800" : "text-gray-700"}`}>
      <span aria-hidden>{icon}</span>
      {text}
    </span>
  );
}

export function MenteeRow({ row }: { row: Row }) {
  const guide = row.mentorship_type === "guide";
  const met = `${row.meetings_this_term}/${row.meetings_required} meetings`;
  const short = !guide && row.meetings_this_term < row.meetings_required;

  return (
    <li
      className={`card flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between ${
        row.needs_attention ? "border-l-4 border-l-amber-500" : ""
      }`}
    >
      <div className="flex min-w-0 items-start gap-3">
        <Avatar name={row.name} />
        <div className="min-w-0 space-y-1.5">
          <p className="flex flex-wrap items-center gap-2">
            {row.needs_attention ? <AlertTriangle aria-label="Needs attention" size={16} className="text-amber-600" /> : null}
            <span className="font-black text-gray-900">{row.name}</span>
            <span className="text-xs font-medium text-gray-600">{row.roll_no}</span>
          </p>
          {row.attention_reasons.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {row.attention_reasons.map((r) => (
                <AttentionBadge key={r} reason={r} detail={row.attention_details?.[r]} />
              ))}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {!guide ? <Stat icon={<CalendarClock size={14} />} text={met} warn={short} /> : null}
            <Stat icon={<CalendarClock size={14} />} text={`Last session ${row.last_session_date ? formatRelative(row.last_session_date) : "none yet"}`} />
            <Stat
              icon={<ClipboardList size={14} />}
              text={`${row.open_actions} open action${row.open_actions === 1 ? "" : "s"}${row.overdue_actions ? ` · ${row.overdue_actions} overdue` : ""}`}
              warn={row.overdue_actions > 0}
            />
            {row.open_issues > 0 ? (
              <Stat icon={<MessageSquareWarning size={14} />} text={`${row.open_issues} open issue${row.open_issues === 1 ? "" : "s"}`} warn />
            ) : null}
            {row.unconfirmed_sessions > 0 ? (
              <Stat icon={<CalendarClock size={14} />} text={`${row.unconfirmed_sessions} unconfirmed session${row.unconfirmed_sessions === 1 ? "" : "s"}`} />
            ) : null}
          </div>
        </div>
      </div>
      <div className="flex shrink-0 gap-2">
        <Link href={`/faculty/mentees/${row.student_id}`} className="btn-secondary">
          Open<span className="sr-only"> {row.name}</span>
        </Link>
        <Link href={`/faculty/sessions/new?student=${row.student_id}`} className="btn-ghost border border-gray-200">
          Log session<span className="sr-only"> for {row.name}</span>
        </Link>
      </div>
    </li>
  );
}
