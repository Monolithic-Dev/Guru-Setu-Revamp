// One certificate and its status (FLOW-02 step 3). Status is text first; colour only reinforces it.
import { BadgeCheck, Clock, FileText, Loader2, Star } from "lucide-react";
import { StatusPill } from "@/components/ui";
import { formatDate } from "@/lib/format";
import type { components } from "@/lib/types";
import { capitalise, reasonLines } from "./reasons";

type Certificate = components["schemas"]["Certificate"];

export interface CertificateCardProps {
  certificate: Certificate;
  /** True when polling stopped after 30 s while still processing. */
  stillWorking?: boolean;
  onManual?: (certificate: Certificate) => void;
}

const ACCENT: Record<Certificate["status"], string> = {
  processing: "border-l-blue-500",
  certified: "border-l-green-600",
  needs_review: "border-l-amber-500",
  duplicate: "border-l-gray-400",
  failed: "border-l-red-600",
  rejected: "border-l-red-600",
};

const OUTPUT_LABEL: Record<NonNullable<Certificate["output_type"]>, string> = {
  report: "Report", prototype: "Prototype", paper: "Paper", dataset: "Dataset", other: "Other output",
};

/** A project record (REQ-040): written by the guide who vouches for the work, so there is no file and no confidence. */
function ProjectRecordCard({ certificate: c }: { certificate: Certificate }) {
  return (
    <article className="card border-l-4 border-l-blue-600" aria-labelledby={`cert-${c.id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span aria-hidden className="mt-0.5 rounded-xl bg-blue-50 p-2 text-blue-800">
            <Star size={20} />
          </span>
          <div className="min-w-0">
            <h3 id={`cert-${c.id}`} className="font-black text-gray-900">
              Project: {c.title ?? "Guided work"}
            </h3>
            <p className="text-sm text-gray-600">
              Guided by {c.recorded_by ?? "your guide"}
              {c.issue_date ? ` · ${formatDate(c.issue_date)}` : ""}
              {c.output_type ? ` · ${OUTPUT_LABEL[c.output_type]}` : ""}
            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-0.5 text-[11px] font-bold text-blue-800">
          <Star aria-hidden size={12} /> Faculty-verified
        </span>
      </div>
      {c.summary ? <p className="mt-3 whitespace-pre-wrap text-sm text-gray-800">{c.summary}</p> : null}
      {c.skills.length > 0 ? (
        <ul className="mt-3 flex flex-wrap gap-2" aria-label="Skills vouched for">
          {c.skills.map((s) => (
            <li key={s} className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-900">
              <Star aria-hidden size={12} />
              {s}
              <span className="sr-only"> (Faculty-verified)</span>
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

export function CertificateCard({ certificate: c, stillWorking = false, onManual }: CertificateCardProps) {
  if (c.kind === "project_record") return <ProjectRecordCard certificate={c} />;
  const meta = [c.issuer, c.issue_date ? formatDate(c.issue_date) : null, c.level && c.level !== "unknown" ? capitalise(c.level) : null]
    .filter(Boolean)
    .join(" · ");
  const lines = c.status === "certified" || c.status === "processing" ? [] : reasonLines(c.reasons);

  return (
    <article className={`card border-l-4 ${ACCENT[c.status]}`} aria-labelledby={`cert-${c.id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span aria-hidden className="mt-0.5 rounded-xl bg-brand-soft p-2 text-brand">
            {c.status === "processing" ? <Loader2 size={20} className="animate-spin" /> : <FileText size={20} />}
          </span>
          <div className="min-w-0">
            <h3 id={`cert-${c.id}`} className="font-black text-gray-900">
              {c.status === "processing" ? "Reading certificate…" : c.title ?? "Untitled certificate"}
            </h3>
            {meta && c.status !== "processing" ? <p className="text-sm text-gray-600">{meta}</p> : null}
          </div>
        </div>
        <StatusPill status={c.status} />
      </div>

      {c.status === "processing" && stillWorking ? (
        <p className="mt-3 flex items-center gap-2 text-sm font-bold text-blue-800" role="status">
          <Clock aria-hidden size={16} /> Still working. We&apos;ll notify you.
        </p>
      ) : null}

      {lines.length > 0 ? (
        <ul className="mt-3 space-y-1">
          {lines.map((line) => (
            <li key={line} className="text-sm font-medium text-gray-800">
              {line}
            </li>
          ))}
        </ul>
      ) : null}

      {c.status === "rejected" && c.review_reason ? (
        <p className="mt-2 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-900">
          <span className="font-bold">Reviewer&apos;s note:</span> {c.review_reason}
        </p>
      ) : null}

      {c.status !== "processing" && c.skills.length > 0 ? (
        <ul className="mt-3 flex flex-wrap gap-2" aria-label="Skills on this certificate">
          {c.skills.map((s) => (
            <li
              key={s}
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-bold ${
                c.status === "certified" ? "border-green-200 bg-green-50 text-green-900" : "border-gray-200 bg-gray-50 text-gray-700"
              }`}
            >
              {c.status === "certified" ? <BadgeCheck aria-hidden size={12} /> : null}
              {s}
              {c.status === "certified" ? <span className="sr-only"> (Certified)</span> : null}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        {c.confidence != null && c.status !== "processing" ? (
          <p className="text-xs font-bold text-gray-600">Confidence {c.confidence.toFixed(2)}</p>
        ) : (
          <span />
        )}
        {c.status === "failed" && onManual ? (
          <button type="button" className="btn-secondary" onClick={() => onManual(c)}>
            Enter details
          </button>
        ) : null}
      </div>
    </article>
  );
}
