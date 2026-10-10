"use client";
// Issues on Mentee 360 (REQ-011, API-032). Text is shown only when the server sends it (security §4):
// a missing `text` renders nothing, never an empty box.
import { useState } from "react";
import { EyeOff, ShieldAlert } from "lucide-react";
import { Dialog, StatusPill, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type Issue = components["schemas"]["Issue"];
type IssuePatch = components["schemas"]["IssuePatch"];

export interface IssueListProps {
  issues: Issue[];
  /** Viewer may act: the mentor on their mentee's issues; the HOD on escalated ones. */
  canEdit: (issue: Issue) => boolean;
  onChanged: () => void;
}

const CATEGORY: Record<string, string> = {
  academic: "Academic",
  attendance: "Attendance",
  career: "Career",
  research: "Research",
  personal: "Personal",
  other: "Other",
};

export function IssueList({ issues, canEdit, onChanged }: IssueListProps) {
  const toast = useToast();
  const [resolving, setResolving] = useState<Issue | null>(null);
  const [note, setNote] = useState("");
  const [noteError, setNoteError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function patch(issue: Issue, body: IssuePatch, success: string): Promise<boolean> {
    setBusy(true);
    try {
      await api.patch(`/issues/${issue.id}`, body);
      toast.success(success);
      onChanged();
      return true;
    } catch (e) {
      if (isApiError(e) && e.status === 422) {
        setNoteError(e.errors[0]?.message ?? "Add a resolution note.");
        return false;
      }
      toast.error(isApiError(e) && e.code === "INVALID_TRANSITION" ? e.detail ?? "This issue changed. Refreshing." : "Couldn't update. Try again.");
      onChanged();
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function submitResolve() {
    if (!resolving) return;
    const text = note.trim();
    if (!text) {
      setNoteError("Add a resolution note.");
      document.getElementById("resolve-note")?.focus();
      return;
    }
    if (await patch(resolving, { status: "resolved", resolution: text }, "Issue resolved")) closeResolve();
  }

  function closeResolve() {
    setResolving(null);
    setNote("");
    setNoteError(null);
  }

  if (issues.length === 0) return <p className="text-sm text-gray-600">No issues raised.</p>;
  const ordered = [...issues].sort((a, b) => Number(a.status === "resolved") - Number(b.status === "resolved") || b.raised_at.localeCompare(a.raised_at));

  return (
    <>
      <ul className="space-y-2">
        {ordered.map((issue) => (
          <li key={issue.id} className="rounded-2xl border border-gray-200 bg-white p-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <p className="flex flex-wrap items-center gap-2 text-sm font-black text-gray-900">
                {CATEGORY[issue.category] ?? issue.category}
                <span className="text-xs font-medium text-gray-600">
                  raised {formatDate(issue.raised_at)} by {issue.raised_by_role === "student" ? "the student" : "the mentor"}
                </span>
              </p>
              <div className="flex flex-wrap gap-1">
                {issue.escalated ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-brand-line bg-brand-soft px-2 py-0.5 text-[11px] font-black uppercase text-brand">
                    <ShieldAlert aria-hidden size={12} /> Escalated
                  </span>
                ) : null}
                {issue.confidential ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-gray-300 bg-gray-100 px-2 py-0.5 text-[11px] font-black uppercase text-gray-700">
                    <EyeOff aria-hidden size={12} /> Confidential
                  </span>
                ) : null}
                <StatusPill status={issue.status} />
              </div>
            </div>
            {issue.text ? <p className="mt-2 text-sm text-gray-800">{issue.text}</p> : null}
            {issue.status === "resolved" && issue.resolution ? (
              <p className="mt-2 rounded-xl bg-green-50 px-3 py-2 text-sm text-green-900">
                <span className="font-bold">Resolution ({formatDate(issue.resolved_at)}):</span> {issue.resolution}
              </p>
            ) : null}
            {canEdit(issue) && issue.status !== "resolved" ? (
              <div className="mt-2 flex flex-wrap gap-2">
                <button type="button" className="btn-primary px-4 py-2 text-xs" disabled={busy} onClick={() => setResolving(issue)}>
                  Resolve<span className="sr-only"> {CATEGORY[issue.category]} issue</span>
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>

      <Dialog
        open={resolving !== null}
        onClose={closeResolve}
        size="sm"
        title="Resolve issue"
        description="Describe how it was resolved. The note is counted, never exported as text."
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={closeResolve}>
              Cancel
            </button>
            <button type="button" className="btn-primary" disabled={busy} onClick={() => void submitResolve()}>
              Resolve
            </button>
          </>
        }
      >
        <label htmlFor="resolve-note" className="label">
          Resolution note
        </label>
        <textarea
          id="resolve-note"
          className="input"
          rows={3}
          maxLength={1000}
          value={note}
          onChange={(e) => {
            setNote(e.target.value);
            setNoteError(null);
          }}
          aria-invalid={!!noteError}
          aria-describedby={noteError ? "resolve-note-error" : undefined}
        />
        {noteError ? (
          <p id="resolve-note-error" role="alert" className="mt-1 text-xs font-bold text-red-700">
            {noteError}
          </p>
        ) : null}
      </Dialog>
    </>
  );
}
