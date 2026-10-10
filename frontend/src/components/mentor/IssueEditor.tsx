"use client";
// Repeater for issues raised in a session (FLOW-07): student, category, text, confidential (add-on A4, REQ-036).
import { Plus, Trash2 } from "lucide-react";
import { TOPICS, type Topic } from "./TopicChips";

export interface IssueDraft {
  key: string;
  student_id: string;
  category: Topic;
  text: string;
  confidential: boolean;
}

export interface IssueEditorProps {
  items: IssueDraft[];
  students: { id: string; name: string }[];
  errors: Record<string, string>;
  onChange: (items: IssueDraft[]) => void;
  onAdd: () => void;
  max?: number;
}

export function IssueEditor({ items, students, errors, onChange, onAdd, max = 10 }: IssueEditorProps) {
  const update = (i: number, patch: Partial<IssueDraft>) => onChange(items.map((it, j) => (j === i ? { ...it, ...patch } : it)));
  const fid = (i: number, f: string) => `sf-issues-${i}-${f}`;
  const err = (i: number, f: string) => errors[`issues.${i}.${f}`];
  const desc = (i: number, f: string) => (err(i, f) ? { "aria-invalid": true, "aria-describedby": `${fid(i, f)}-error` } : {});
  const msg = (i: number, f: string) =>
    err(i, f) ? (
      <p id={`${fid(i, f)}-error`} role="alert" className="mt-1 text-xs font-bold text-red-700">
        {err(i, f)}
      </p>
    ) : null;

  return (
    <div className="space-y-3">
      {items.map((it, i) => (
        <fieldset key={it.key} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
          <legend className="px-1 text-xs font-black uppercase tracking-widest text-gray-600">Issue {i + 1}</legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor={fid(i, "student_id")} className="label">
                Student
              </label>
              <select id={fid(i, "student_id")} className="input" value={it.student_id} onChange={(e) => update(i, { student_id: e.target.value })} {...desc(i, "student_id")}>
                <option value="">Choose a student</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              {msg(i, "student_id")}
            </div>
            <div>
              <label htmlFor={fid(i, "category")} className="label">
                Category
              </label>
              <select id={fid(i, "category")} className="input" value={it.category} onChange={(e) => update(i, { category: e.target.value as Topic })}>
                {TOPICS.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor={fid(i, "text")} className="label">
                Describe the issue
              </label>
              <div className="flex gap-2">
                <textarea id={fid(i, "text")} className="input" rows={2} maxLength={1000} value={it.text} onChange={(e) => update(i, { text: e.target.value })} {...desc(i, "text")} />
                <button type="button" aria-label={`Remove issue ${i + 1}`} className="btn-ghost shrink-0 self-start text-red-700" onClick={() => onChange(items.filter((_, j) => j !== i))}>
                  <Trash2 aria-hidden size={18} />
                </button>
              </div>
              {msg(i, "text")}
            </div>
            <label className="inline-flex min-h-[40px] cursor-pointer items-center gap-2 text-sm font-bold text-gray-700 sm:col-span-2">
              <input
                type="checkbox"
                className="h-4 w-4 accent-brand"
                checked={it.confidential}
                onChange={(e) => update(i, { confidential: e.target.checked })}
                aria-describedby={`${fid(i, "confidential")}-help`}
              />
              Confidential
              <span id={`${fid(i, "confidential")}-help`} className="text-xs font-medium text-gray-600">
                Counted only as &quot;confidential&quot;; text visible to you and the student.
              </span>
            </label>
          </div>
        </fieldset>
      ))}
      {items.length < max ? (
        <button type="button" className="btn-secondary" onClick={onAdd} disabled={students.length === 0}>
          <Plus aria-hidden size={16} /> Add issue
        </button>
      ) : null}
    </div>
  );
}
