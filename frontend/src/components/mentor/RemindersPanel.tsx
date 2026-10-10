"use client";
// Reminders (add-on A3, REQ-023, API-039), computed by the server when the list is opened.
// P4's SCR-14 renders it at the top behind `features.reminders`. Renders nothing when there are none.
import Link from "next/link";
import { useEffect, useState } from "react";
import { BellRing, CalendarClock, ClipboardList, MessageSquareWarning, UserCheck } from "lucide-react";
import { ErrorState } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { formatDate } from "@/lib/format";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

type Reminder = components["schemas"]["Reminder"];

export type RemindersPanelProps = Record<string, never>;

const ICON: Record<Reminder["kind"], typeof BellRing> = {
  meetings_due: CalendarClock,
  action_overdue: ClipboardList,
  issue_stale: MessageSquareWarning,
  session_unconfirmed: UserCheck,
};

export default function RemindersPanel() {
  const { data, error, reload } = useApi<Reminder[]>("/me/reminders");
  const [student, setStudent] = useState(false);
  useEffect(() => setStudent(getSession()?.role === "student"), []);

  if (error) return <ErrorState inline error={error} onRetry={reload} />;
  if (!data || data.length === 0) return null;

  const hrefFor = (r: Reminder) => (student || !r.student_id ? "/student/mentorship" : `/faculty/mentees/${r.student_id}`);

  return (
    <section aria-labelledby="reminders-title" className="card space-y-3 border-gold-line bg-gold-soft">
      <h2 id="reminders-title" className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-gold-ink">
        <BellRing aria-hidden size={16} /> Reminders ({data.length})
      </h2>
      <ul className="space-y-2">
        {data.map((r) => {
          const Icon = ICON[r.kind];
          return (
            <li key={`${r.kind}-${r.ref_id}`}>
              <Link href={hrefFor(r)} className="flex items-start gap-3 rounded-2xl bg-white px-3 py-2.5 hover:shadow-md">
                <Icon aria-hidden size={18} className="mt-0.5 shrink-0 text-brand" />
                <span className="text-sm">
                  <span className="font-bold text-gray-900">{r.message}</span>
                  {r.due_date ? <span className="block text-xs text-gray-600">Due {formatDate(r.due_date)}</span> : null}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
