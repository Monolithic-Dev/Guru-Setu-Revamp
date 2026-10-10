import { BadgeCheck, Circle, Star } from "lucide-react";

// Trust levels (PRD §4): 0 Claimed, 1 Certified, 2 Faculty-verified. Text label always present (ux-flows §7).
const LEVELS = {
  0: { label: "Claimed", cls: "border-gray-300 bg-white text-gray-700", Icon: Circle },
  1: { label: "Certified", cls: "border-green-200 bg-green-50 text-green-800", Icon: BadgeCheck },
  2: { label: "Faculty-verified", cls: "border-blue-200 bg-blue-50 text-blue-800", Icon: Star },
} as const;

export interface TrustBadgeProps {
  level: 0 | 1 | 2;
  /** Shown after the label, e.g. the certificate title or endorsing faculty ("Certified · NPTEL Deep Learning"). */
  source?: string;
}

export function TrustBadge({ level, source }: TrustBadgeProps) {
  const { label, cls, Icon } = LEVELS[level];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-bold ${cls}`}>
      <Icon aria-hidden size={12} strokeWidth={2.5} />
      {label}
      {source ? <span className="font-medium"> · {source}</span> : null}
    </span>
  );
}
