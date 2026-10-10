"use client";
// Faculty endorsement (REQ-027, API-041): a named mentor vouches for one skill, which lifts it to Faculty-verified.
// It is a human claim with the mentor's name on it, so it asks for a confirmation first. The server decides the
// trust level; this component only sends the concept and hands the returned profile back.
import { useState } from "react";
import { Star } from "lucide-react";
import { Dialog, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type StudentProfile = components["schemas"]["StudentProfile"];

export interface EndorseButtonProps {
  studentId: string;
  studentName: string;
  concept: string;
  onEndorsed: (profile: StudentProfile) => void;
}

export function EndorseButton({ studentId, studentName, concept, onEndorsed }: EndorseButtonProps) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post<StudentProfile>(`/students/${studentId}/endorsements`, { concept });
      onEndorsed(data);
      setOpen(false);
      toast.success(`Endorsed ${concept}.`);
    } catch (err) {
      setError(isApiError(err) ? err.detail || "Couldn't endorse this skill." : "Couldn't endorse this skill. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="btn-ghost !min-h-[44px] !px-2 text-xs text-brand"
        aria-label={`Endorse ${concept} for ${studentName}`}
        onClick={() => {
          setError(null);
          setOpen(true);
        }}
      >
        <Star aria-hidden size={14} /> Endorse
      </button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={`Endorse ${concept}?`}
        description={`Say this only if you have worked with ${studentName} on it. It will show as Faculty-verified with your name.`}
        size="sm"
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button type="button" className="btn-primary" disabled={busy} onClick={() => void confirm()}>
              {busy ? "Saving…" : "Endorse"}
            </button>
          </>
        }
      >
        {error ? (
          <p role="alert" className="text-sm font-bold text-red-700">
            {error}
          </p>
        ) : (
          <p className="text-sm text-gray-700">You can&apos;t undo this from here, so check the skill name first.</p>
        )}
      </Dialog>
    </>
  );
}
