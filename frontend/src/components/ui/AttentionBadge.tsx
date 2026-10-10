import { AlertTriangle } from "lucide-react";

export type AttentionReason =
  | "no_recent_session"
  | "no_meeting_this_term"
  | "overdue_action"
  | "stale_issue"
  | "marked_at_risk"
  | "suggested_at_risk";

// Labels from ux-flows §4.3. Day numbers are the defaults (A-20).
const LABELS: Record<AttentionReason, string> = {
  no_recent_session: "Not met in 45+ days",
  no_meeting_this_term: "No meeting this term",
  overdue_action: "Overdue action",
  stale_issue: "Issue open 14+ days",
  marked_at_risk: "Marked at risk",
  suggested_at_risk: "Suggested at risk",
};

export function attentionLabel(reason: AttentionReason, detail?: string | null): string {
  if (reason === "suggested_at_risk" && detail) return `Suggested at risk: ${detail}`;
  return LABELS[reason] ?? reason;
}

export interface AttentionBadgeProps {
  reason: AttentionReason;
  detail?: string | null;
}

export function AttentionBadge({ reason, detail }: AttentionBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-900">
      <AlertTriangle aria-hidden size={12} strokeWidth={2.5} />
      {attentionLabel(reason, detail)}
    </span>
  );
}
