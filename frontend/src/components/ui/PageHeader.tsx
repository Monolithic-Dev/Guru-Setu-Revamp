import Link from "next/link";
import type { ReactNode } from "react";
import { ChevronLeft } from "lucide-react";

export interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
  /** Back link (the earlier GuruSetu screens always offered one on detail pages). */
  backHref?: string;
  backLabel?: string;
  actions?: ReactNode;
}

export function PageHeader({ title, subtitle, backHref, backLabel = "Back", actions }: PageHeaderProps) {
  return (
    <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        {backHref ? (
          <Link href={backHref} className="mb-2 inline-flex items-center gap-1 text-xs font-black uppercase tracking-widest text-brand hover:underline">
            <ChevronLeft aria-hidden size={16} />
            {backLabel}
          </Link>
        ) : null}
        <h1 className="text-2xl font-black tracking-tight text-gray-900">{title}</h1>
        {subtitle ? <div className="mt-1 text-sm font-medium text-gray-600">{subtitle}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}
