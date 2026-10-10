import type { ReactNode } from "react";
import { formatDate } from "@/lib/format";

export interface TimelineEvent {
  id: string;
  /** YYYY-MM-DD or an ISO timestamp; events are shown newest first. */
  date: string;
  title: string;
  detail?: ReactNode;
  kind?: "session" | "action" | "issue" | "status" | "certificate" | "application";
}

const DOT: Record<NonNullable<TimelineEvent["kind"]>, string> = {
  session: "bg-brand",
  action: "bg-gold",
  issue: "bg-amber-600",
  status: "bg-gray-400",
  certificate: "bg-green-600",
  application: "bg-blue-600",
};

const KIND_LABEL: Record<NonNullable<TimelineEvent["kind"]>, string> = {
  session: "Session",
  action: "Action item",
  issue: "Issue",
  status: "Status change",
  certificate: "Certificate",
  application: "Application",
};

export function Timeline({ events, emptyText = "Nothing recorded yet." }: { events: TimelineEvent[]; emptyText?: string }) {
  if (events.length === 0) return <p className="text-sm text-gray-600">{emptyText}</p>;
  const sorted = [...events].sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
  return (
    <ol className="relative space-y-4 border-l-2 border-gray-200 pl-5">
      {sorted.map((e) => (
        <li key={e.id} className="relative">
          <span aria-hidden className={`absolute -left-[27px] top-1.5 h-3 w-3 rounded-full ring-4 ring-white ${DOT[e.kind ?? "status"]}`} />
          <p className="text-[11px] font-bold uppercase tracking-wider text-gray-600">
            {formatDate(e.date)}
            {e.kind ? ` · ${KIND_LABEL[e.kind]}` : ""}
          </p>
          <p className="text-sm font-bold text-gray-900">{e.title}</p>
          {e.detail ? <div className="mt-0.5 text-sm text-gray-700">{e.detail}</div> : null}
        </li>
      ))}
    </ol>
  );
}
