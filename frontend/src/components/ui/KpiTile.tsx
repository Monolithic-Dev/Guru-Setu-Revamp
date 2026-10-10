import Link from "next/link";
import { ChevronRight } from "lucide-react";

export interface KpiTileProps {
  label: string;
  value: string | number;
  sub?: string;
  /** Click-to-source drill-down (add-on A1). When set, the tile is a link. */
  href?: string;
  /** Draw attention (for example compliance below 100%). */
  highlight?: boolean;
}

export function KpiTile({ label, value, sub, href, highlight = false }: KpiTileProps) {
  const body = (
    <>
      <p className="text-[11px] font-black uppercase tracking-widest text-gray-600">{label}</p>
      <p className={`mt-1 text-2xl font-black ${highlight ? "text-brand" : "text-gray-900"}`}>{value}</p>
      {sub ? <p className="mt-0.5 text-xs font-medium text-gray-600">{sub}</p> : null}
    </>
  );
  const cls = `card block p-4 ${highlight ? "border-brand-line bg-brand-tint" : ""}`;
  if (href) {
    return (
      <Link href={href} className={`${cls} group relative transition-shadow hover:shadow-md`}>
        {body}
        <ChevronRight aria-hidden size={16} className="absolute right-3 top-4 text-gray-500 group-hover:text-brand" />
        <span className="sr-only">, view records</span>
      </Link>
    );
  }
  return <div className={cls}>{body}</div>;
}
