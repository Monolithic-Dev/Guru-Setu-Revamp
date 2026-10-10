"use client";
// Completing guided work (REQ-040, API-018): the guide writes what was done and vouches for the skills it showed.
// This becomes a project record on the student's profile and Faculty-verified skills with the guide's name, so it
// asks for a confirmation and says plainly that it cannot be edited afterwards. There is no grade or rating field.
import { useEffect, useState } from "react";
import { Dialog } from "@/components/ui";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type Completion = components["schemas"]["ProjectCompletion"];
type Output = Completion["output_type"];

const OUTPUTS: { value: Output; label: string }[] = [
  { value: "report", label: "Report" },
  { value: "prototype", label: "Prototype" },
  { value: "paper", label: "Paper" },
  { value: "dataset", label: "Dataset" },
  { value: "other", label: "Other" },
];
const MIN = 20;
const MAX = 600;

export interface CompleteWorkDialogProps {
  open: boolean;
  onClose: () => void;
  applicationId: string;
  studentName: string;
  openingTitle: string;
  /** The skills the opening required: the guide ticks the ones the work really showed. */
  skills: string[];
  onDone: () => void;
}

export function CompleteWorkDialog({ open, onClose, applicationId, studentName, openingTitle, skills, onDone }: CompleteWorkDialogProps) {
  const [summary, setSummary] = useState("");
  const [picked, setPicked] = useState<string[]>(skills);
  const [output, setOutput] = useState<Output>("report");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSummary("");
      setPicked(skills);
      setOutput("report");
      setError(null);
    }
  }, [open, skills]);

  const length = summary.trim().length;
  const valid = length >= MIN && length <= MAX && picked.length > 0;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid) return;
    setBusy(true);
    setError(null);
    try {
      const completion: Completion = { summary: summary.trim(), skills: picked, output_type: output };
      await api.patch(`/applications/${applicationId}`, { status: "completed", completion });
      onDone();
    } catch (err) {
      setError(isApiError(err) && err.detail ? err.detail : "Couldn't save the record. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Complete ${studentName}'s work`}
      description={`${openingTitle}. This leaves a project record on their profile. You can't edit it afterwards.`}
      size="md"
      footer={
        <>
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" form="complete-form" className="btn-primary" disabled={busy || !valid}>
            {busy ? "Saving…" : "Record and complete"}
          </button>
        </>
      }
    >
      <form id="complete-form" onSubmit={submit} noValidate className="space-y-4">
        <div>
          <label htmlFor="cw-summary" className="label">What did they do?</label>
          <textarea
            id="cw-summary"
            className="input min-h-[110px]"
            value={summary}
            maxLength={MAX}
            onChange={(e) => setSummary(e.target.value)}
            aria-describedby="cw-summary-hint"
          />
          <p id="cw-summary-hint" className={`mt-1 text-xs ${length > 0 && length < MIN ? "font-bold text-red-700" : "text-gray-600"}`}>
            {length}/{MAX} characters, at least {MIN}. Describe the work, not how good it was.
          </p>
        </div>

        <fieldset>
          <legend className="label">Skills you vouch for</legend>
          {skills.length === 0 ? (
            <p className="text-sm text-gray-600">This opening lists no required skills.</p>
          ) : (
            <ul className="space-y-1">
              {skills.map((s) => (
                <li key={s}>
                  <label className="flex min-h-[44px] items-center gap-2 text-sm font-bold text-gray-900">
                    <input
                      type="checkbox"
                      className="h-5 w-5 accent-[#8c1515]"
                      checked={picked.includes(s)}
                      onChange={(e) => setPicked((cur) => (e.target.checked ? [...cur, s] : cur.filter((x) => x !== s)))}
                    />
                    {s}
                  </label>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-1 text-xs text-gray-600">Each ticked skill will show as Faculty-verified with your name.</p>
        </fieldset>

        <div>
          <label htmlFor="cw-output" className="label">What did the work produce?</label>
          <select id="cw-output" className="input" value={output} onChange={(e) => setOutput(e.target.value as Output)}>
            {OUTPUTS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {error ? (
          <p role="alert" className="text-sm font-bold text-red-700">
            {error}
          </p>
        ) : null}
      </form>
    </Dialog>
  );
}
