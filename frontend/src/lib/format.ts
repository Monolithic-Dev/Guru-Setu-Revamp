// Display formats (ux-flows §4.4). Calendar dates are Asia/Kolkata (architecture §5).
const TZ = "Asia/Kolkata";

function toDate(value: string): Date {
  // A bare YYYY-MM-DD is a calendar date: anchor it at IST noon so it never shifts a day.
  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T12:00:00+05:30`) : new Date(value);
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "10 Oct 2026" (fixed three-letter months; en-GB would print "Sept"). */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = toDate(value);
  if (Number.isNaN(d.getTime())) return "—";
  const [y, m, day] = todayIst(d).split("-").map(Number);
  return `${day} ${MONTHS[m - 1]} ${y}`;
}

/** "3 days ago" when within 14 days, otherwise the absolute date. */
export function formatRelative(value: string | null | undefined, now: Date = new Date()): string {
  if (!value) return "—";
  const d = toDate(value);
  if (Number.isNaN(d.getTime())) return "—";
  const dayMs = 86_400_000;
  const days = Math.round((startOfDayIst(now) - startOfDayIst(d)) / dayMs);
  if (days < 0 || days > 14) return formatDate(value);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

function startOfDayIst(d: Date): number {
  const ymd = new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(d); // YYYY-MM-DD
  return new Date(`${ymd}T00:00:00+05:30`).getTime();
}

/** Today's calendar date in IST as YYYY-MM-DD. */
export function todayIst(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(now);
}

export function addDays(ymd: string, days: number): string {
  const d = new Date(`${ymd}T12:00:00+05:30`);
  d.setUTCDate(d.getUTCDate() + days);
  return todayIst(d);
}

/** Scores: one decimal. */
export const formatScore = (n: number | null | undefined) => (n == null ? "—" : n.toFixed(1));

/** Percentages: one decimal with %. */
export const formatPct = (n: number | null | undefined) => (n == null ? "—" : `${n.toFixed(1)}%`);

export function initials(name: string): string {
  const parts = name
    .replace(/^(dr|mr|ms|mrs|prof)\.?\s+/i, "")
    .split(/\s+/)
    .filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase() || "?";
}

export function firstName(name: string): string {
  return name.replace(/^(dr|mr|ms|mrs|prof)\.?\s+/i, "").split(/\s+/)[0] ?? name;
}
