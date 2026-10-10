"use client";
// One certificate in the review queue (FLOW-05, REQ-002). Preview comes from API-011 as a blob (SEC-19).
import { useEffect, useState } from "react";
import { Check, ExternalLink, FileWarning, X } from "lucide-react";
import { reasonLines } from "@/components/certificates/reasons";
import { Avatar, StatusPill } from "@/components/ui";
import { fetchObjectUrl } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { components } from "@/lib/types";

type ReviewItem = components["schemas"]["ReviewItem"];

export interface ReviewCardProps {
  item: ReviewItem;
  busy?: boolean;
  onApprove: (item: ReviewItem) => void;
  onReject: (item: ReviewItem) => void;
}

function Preview({ certificateId, mediaType, title }: { certificateId: string; mediaType: string; title: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let url: string | null = null;
    let cancelled = false;
    fetchObjectUrl(`/certificates/${certificateId}/file`)
      .then((res) => {
        url = res.url;
        if (cancelled) URL.revokeObjectURL(res.url);
        else setSrc(res.url);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [certificateId]);

  if (failed) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-2xl bg-gray-100 text-sm font-bold text-gray-600">
        <FileWarning aria-hidden size={28} /> Preview unavailable
      </div>
    );
  }
  if (!src) return <div aria-hidden className="h-48 animate-pulse rounded-2xl bg-gray-200" />;
  return (
    <div className="space-y-2">
      {mediaType === "application/pdf" ? (
        <iframe sandbox="" src={src} title={`Certificate file: ${title}`} className="h-64 w-full rounded-2xl border border-gray-200 bg-white" />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element -- blob URL from the authenticated API, not a static asset
        <img src={src} alt={`Certificate file: ${title}`} className="max-h-72 w-full rounded-2xl border border-gray-200 bg-white object-contain" />
      )}
      <a href={src} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-black text-brand underline underline-offset-2">
        Open file <ExternalLink aria-hidden size={12} />
      </a>
    </div>
  );
}

export function ReviewCard({ item, busy = false, onApprove, onReject }: ReviewCardProps) {
  const c = item.certificate;
  const title = c.title ?? "Untitled certificate";
  const fields: [string, string | null | undefined][] = [
    ["Name on certificate", c.holder_name],
    ["Issuer", c.issuer],
    ["Issue date", c.issue_date ? formatDate(c.issue_date) : null],
    ["Level", c.level],
    ["Type", c.type],
    ["Certificate ID", c.certificate_id],
  ];

  return (
    <article className="card" aria-labelledby={`review-${c.id}`}>
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <Avatar name={item.student.name} />
          <div>
            <h2 id={`review-${c.id}`} className="font-black text-gray-900">
              {item.student.name} · {title}
            </h2>
            <p className="text-sm text-gray-600">{item.student.roll_no}</p>
          </div>
        </div>
        <StatusPill status={c.status} />
      </header>

      <div className="grid gap-5 md:grid-cols-2">
        <Preview certificateId={c.id} mediaType={c.media_type} title={title} />
        <div className="space-y-4">
          <ul className="space-y-1" aria-label="Why it needs review">
            {reasonLines(c.reasons).map((line) => (
              <li key={line} className="rounded-xl bg-amber-50 px-3 py-2 text-sm font-bold text-amber-900">
                {line}
              </li>
            ))}
            {item.duplicate_of ? (
              <li className="rounded-xl bg-gray-100 px-3 py-2 text-sm text-gray-800">Matches certificate {item.duplicate_of}</li>
            ) : null}
          </ul>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
            {fields.map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="font-bold text-gray-600">{k}</dt>
                <dd className="text-gray-900">{v || "—"}</dd>
              </div>
            ))}
            <dt className="font-bold text-gray-600">Skills</dt>
            <dd className="text-gray-900">{c.skills.length ? c.skills.join(", ") : "—"}</dd>
            {c.confidence != null ? (
              <>
                <dt className="font-bold text-gray-600">Confidence</dt>
                <dd className="text-gray-900">{c.confidence.toFixed(2)}</dd>
              </>
            ) : null}
          </dl>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-primary" disabled={busy} onClick={() => onApprove(item)}>
              <Check aria-hidden size={16} /> Approve<span className="sr-only"> {title} for {item.student.name}</span>
            </button>
            <button type="button" className="btn-secondary" disabled={busy} onClick={() => onReject(item)}>
              <X aria-hidden size={16} /> Reject<span className="sr-only"> {title} for {item.student.name}</span>
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
