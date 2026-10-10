"use client";
// SCR-09 Candidates (FLOW-04; REQ-005, 006): applicants ranked by fit, expandable to their read-only fit,
// with status actions. Applicants only: non-applicants are never listed (NG-11).
import { useParams } from "next/navigation";
import { useState } from "react";
import { ChevronDown, Users } from "lucide-react";
import { CandidateFit } from "@/components/mentor/CandidateFit";
import { Avatar, EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill, useToast } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { formatDate, formatScore } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type Opening = components["schemas"]["Opening"];
type Candidate = components["schemas"]["Candidate"];
type Next = components["schemas"]["ApplicationPatch"]["status"];

const NEXT: Record<string, { to: Next; label: string; primary?: boolean }[]> = {
  pending: [
    { to: "shortlisted", label: "Shortlist", primary: true },
    { to: "rejected", label: "Reject" },
  ],
  shortlisted: [
    { to: "accepted", label: "Accept", primary: true },
    { to: "rejected", label: "Reject" },
  ],
  accepted: [{ to: "completed", label: "Mark completed", primary: true }],
};

const VERDICT_TONE: Record<string, string> = { ready: "accepted", close: "pending", not_yet: "dropped" };
const VERDICT_LABEL: Record<string, string> = { ready: "Ready", close: "Close", not_yet: "Not yet" };

function toastFor(name: string, to: Next): string {
  if (to === "accepted") return `${name} accepted. Guide link created.`;
  if (to === "shortlisted") return `${name} shortlisted.`;
  if (to === "rejected") return `${name} rejected.`;
  return `${name} marked completed.`;
}

export default function CandidatesPage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const opening = useApi<Opening>(`/openings/${id}`);
  const cands = useApi<Candidate[]>(`/openings/${id}/candidates`);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function move(c: Candidate, to: Next) {
    setBusy(c.application.id);
    try {
      await api.patch(`/applications/${c.application.id}`, { status: to });
      toast.success(toastFor(c.student.name, to));
    } catch (e) {
      toast.error(isApiError(e) && e.code === "INVALID_TRANSITION" ? "This application changed. Refreshing." : "Couldn't update. Try again.");
    } finally {
      setBusy(null);
      void cands.reload();
    }
  }

  const ranked = [...(cands.data ?? [])].sort((a, b) => b.fit.score - a.fit.score);

  return (
    <>
      <PageHeader
        title={opening.data?.title ?? "Opening"}
        subtitle={
          opening.data ? (
            <span>
              {ranked.length} applicant{ranked.length === 1 ? "" : "s"} · Required: {opening.data.required_skills.join(", ") || "none listed"}
            </span>
          ) : undefined
        }
        backHref="/faculty/openings"
        backLabel="My openings"
      />
      <p className="mb-4 text-xs font-medium text-gray-600">Ranked by fit to this opening only. Scores never compare students across openings.</p>
      {cands.loading ? (
        <LoadingRegion label="Loading applicants">
          <div className="space-y-3">
            <Skeleton block />
            <Skeleton block />
          </div>
        </LoadingRegion>
      ) : cands.error ? (
        <ErrorState error={cands.error} onRetry={cands.reload} homeHref="/faculty/openings" />
      ) : ranked.length === 0 ? (
        <EmptyState icon={<Users size={36} />} message="No applicants yet." />
      ) : (
        <ol className="space-y-3">
          {ranked.map((c, i) => {
            const expanded = open === c.application.id;
            const panelId = `fit-${c.application.id}`;
            const counts = { matched: 0, claimed_only: 0, near: 0, missing: 0 } as Record<string, number>;
            c.fit.chips.forEach((ch) => (counts[ch.kind] += 1));
            return (
              <li key={c.application.id} className="card p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span aria-hidden className="w-6 text-center text-lg font-black text-gray-500">
                      {i + 1}
                    </span>
                    <Avatar name={c.student.name} />
                    <div className="min-w-0">
                      <p className="font-black text-gray-900">
                        <span className="sr-only">Rank {i + 1}: </span>
                        {c.student.name}
                      </p>
                      <p className="text-xs text-gray-600">
                        {c.student.roll_no} · Year {c.student.year} · Applied {formatDate(c.application.applied_at)}
                      </p>
                      <p className="mt-1 text-xs font-bold text-gray-700">
                        {counts.matched} certified · {counts.claimed_only} claimed only · {counts.near} near · {counts.missing} missing
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-2xl bg-gold px-3 py-1.5 text-center text-gold-ink">
                      <span className="block text-[10px] font-black uppercase tracking-widest">Fit</span>
                      <span className="text-xl font-black">{formatScore(c.fit.score)}</span>
                    </span>
                    <div className="flex flex-col items-end gap-1">
                      <StatusPill status={VERDICT_TONE[c.fit.verdict]} label={VERDICT_LABEL[c.fit.verdict]} />
                      <StatusPill status={c.application.status} />
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                  <button
                    type="button"
                    className="btn-ghost"
                    aria-expanded={expanded}
                    aria-controls={panelId}
                    onClick={() => setOpen(expanded ? null : c.application.id)}
                  >
                    <ChevronDown aria-hidden size={16} className={`transition-transform ${expanded ? "rotate-180" : ""}`} />
                    {expanded ? "Hide fit" : "Show fit"}
                    <span className="sr-only"> for {c.student.name}</span>
                  </button>
                  <div className="flex flex-wrap gap-2">
                    {(NEXT[c.application.status] ?? []).map((a) => (
                      <button
                        key={a.to}
                        type="button"
                        disabled={busy === c.application.id}
                        className={a.primary ? "btn-primary" : "btn-secondary"}
                        onClick={() => void move(c, a.to)}
                      >
                        {a.label}
                        <span className="sr-only"> {c.student.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
                {expanded ? (
                  <div id={panelId} className="mt-4 border-t border-gray-100 pt-4">
                    <CandidateFit fit={c.fit} />
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
    </>
  );
}
