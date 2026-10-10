// Status as text, never colour only (ux-flows §5). One pill for every status enum in the API.

type Tone = "green" | "amber" | "grey" | "red" | "blue" | "brand" | "gold";

const TONES: Record<Tone, string> = {
  green: "bg-green-50 text-green-800 border-green-200",
  amber: "bg-amber-50 text-amber-900 border-amber-200",
  grey: "bg-gray-100 text-gray-700 border-gray-200",
  red: "bg-red-50 text-red-800 border-red-200",
  blue: "bg-blue-50 text-blue-800 border-blue-200",
  brand: "bg-brand-soft text-brand border-brand-line",
  gold: "bg-gold-soft text-gold-ink border-gold-line",
};

/** status value → [label, tone]. Certificate labels follow FLOW-02. */
const STATUS: Record<string, [string, Tone]> = {
  // certificates
  processing: ["Reading certificate…", "blue"],
  certified: ["Verified", "green"],
  needs_review: ["Waiting for review", "amber"],
  duplicate: ["Already uploaded", "grey"],
  failed: ["Couldn't read automatically", "red"],
  rejected: ["Rejected", "red"],
  // applications
  pending: ["Pending", "amber"],
  shortlisted: ["Shortlisted", "blue"],
  accepted: ["Accepted", "green"],
  completed: ["Completed", "grey"],
  // action items
  open: ["Open", "blue"],
  overdue: ["Overdue", "red"],
  done: ["Done", "gold"],
  verified: ["Verified", "green"],
  dropped: ["Dropped", "grey"],
  // issues
  raised: ["Raised", "amber"],
  acknowledged: ["Acknowledged", "blue"],
  in_progress: ["In progress", "blue"],
  resolved: ["Resolved", "green"],
  // sessions
  confirmed: ["Confirmed", "green"],
  unconfirmed: ["Unconfirmed", "amber"],
  // misc
  draft: ["DRAFT", "gold"],
  sample: ["Sample data", "grey"],
};

export function statusLabel(status: string): string {
  return STATUS[status]?.[0] ?? status.replace(/_/g, " ");
}

export interface StatusPillProps {
  status: string;
  /** Override the default label (for example "Applied · Pending"). */
  label?: string;
  className?: string;
}

export function StatusPill({ status, label, className = "" }: StatusPillProps) {
  const [text, tone] = STATUS[status] ?? [statusLabel(status), "grey" as Tone];
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[11px] font-black uppercase tracking-wider ${TONES[tone]} ${className}`}
    >
      {label ?? text}
    </span>
  );
}
