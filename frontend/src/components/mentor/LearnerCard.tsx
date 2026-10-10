"use client";
// Learner level, intervention note and at-risk mark (add-ons B1/B3, REQ-029, REQ-033, API-043).
// Only the assigned mentor sees this card; the server omits learner_note and marked_at_risk for everyone else.
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import { useToast } from "@/components/ui";
import type { components } from "@/lib/types";

type Overview = components["schemas"]["MenteeOverview"];
type Level = NonNullable<Overview["learner_level"]>;

export const LEVEL_LABEL: Record<Level, string> = { slow: "Slow learner", average: "Average learner", advanced: "Advanced learner" };
const NOTE_MAX = 500;

export interface LearnerCardProps {
  studentId: string;
  level: Overview["learner_level"];
  note: Overview["learner_note"];
  atRisk: Overview["marked_at_risk"];
  onSaved: (overview: Overview) => void;
}

export function LearnerCard({ studentId, level, note, atRisk, onSaved }: LearnerCardProps) {
  const toast = useToast();
  const [lvl, setLvl] = useState<string>(level ?? "");
  const [text, setText] = useState(note ?? "");
  const [risk, setRisk] = useState(Boolean(atRisk));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLvl(level ?? "");
    setText(note ?? "");
    setRisk(Boolean(atRisk));
  }, [level, note, atRisk]);

  const dirty = lvl !== (level ?? "") || text.trim() !== (note ?? "").trim() || risk !== Boolean(atRisk);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (text.length > NOTE_MAX) {
      setError(`Keep the note under ${NOTE_MAX} characters.`);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const { data } = await api.patch<Overview>(`/mentees/${studentId}`, {
        learner_level: lvl ? (lvl as Level) : null,
        learner_note: text.trim() || null,
        marked_at_risk: risk,
      });
      onSaved(data);
      toast.success("Saved.");
    } catch (err) {
      const field = isApiError(err) ? err.errors.find((f) => f.field.includes("learner_note"))?.message : undefined;
      setError(field ?? "Couldn't save. Try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save} className="space-y-3" noValidate>
      <div>
        <label htmlFor="lc-level" className="label">
          Learner level
        </label>
        <select id="lc-level" className="input" value={lvl} onChange={(e) => setLvl(e.target.value)}>
          <option value="">Not set</option>
          {(Object.keys(LEVEL_LABEL) as Level[]).map((k) => (
            <option key={k} value={k}>
              {LEVEL_LABEL[k]}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="lc-note" className="label">
          Intervention note <span className="font-normal normal-case text-gray-600">(only you see this)</span>
        </label>
        <textarea
          id="lc-note"
          className="input min-h-[88px]"
          maxLength={NOTE_MAX}
          value={text}
          onChange={(e) => setText(e.target.value)}
          aria-describedby="lc-note-count"
          aria-invalid={error ? true : undefined}
        />
        <p id="lc-note-count" className="mt-1 text-right text-xs text-gray-600">
          {text.length}/{NOTE_MAX}
        </p>
      </div>
      <label className="flex cursor-pointer items-center gap-2 text-sm font-bold text-gray-900">
        <input type="checkbox" role="switch" aria-checked={risk} className="h-4 w-4 accent-brand" checked={risk} onChange={(e) => setRisk(e.target.checked)} />
        At risk
      </label>
      {error ? (
        <p role="alert" className="text-xs font-bold text-red-700">
          {error}
        </p>
      ) : null}
      <button type="submit" className="btn-primary w-full" disabled={saving || !dirty}>
        {saving ? "Saving…" : "Save"}
      </button>
    </form>
  );
}
