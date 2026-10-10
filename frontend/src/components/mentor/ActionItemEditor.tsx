"use client";
// Repeater for action items (FLOW-07): student, text, owner, due date (default session date + 7 days).
import { Plus, Trash2 } from "lucide-react";

export interface ActionDraft {
  key: string;
  student_id: string;
  text: string;
  owner: "mentee" | "mentor";
  due_date: string;
}

export interface ActionItemEditorProps {
  items: ActionDraft[];
  students: { id: string; name: string }[];
  errors: Record<string, string>;
  onChange: (items: ActionDraft[]) => void;
  onAdd: () => void;
  max?: number;
}

export function ActionItemEditor({ items, students, errors, onChange, onAdd, max = 10 }: ActionItemEditorProps) {
  const update = (i: number, patch: Partial<ActionDraft>) => onChange(items.map((it, j) => (j === i ? { ...it, ...patch } : it)));
  const err = (i: number, f: string) => errors[`actions.${i}.${f}`];
  const fid = (i: number, f: string) => `sf-actions-${i}-${f}`;
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
          <legend className="px-1 text-xs font-black uppercase tracking-widest text-gray-600">Action item {i + 1}</legend>
          <div className="grid gap-3 sm:grid-cols-[1fr_1fr]">
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
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor={fid(i, "owner")} className="label">
                  Owner
                </label>
                <select id={fid(i, "owner")} className="input" value={it.owner} onChange={(e) => update(i, { owner: e.target.value as ActionDraft["owner"] })}>
                  <option value="mentee">Mentee</option>
                  <option value="mentor">Mentor</option>
                </select>
              </div>
              <div>
                <label htmlFor={fid(i, "due_date")} className="label">
                  Due
                </label>
                <input id={fid(i, "due_date")} type="date" className="input" value={it.due_date} onChange={(e) => update(i, { due_date: e.target.value })} {...desc(i, "due_date")} />
              </div>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor={fid(i, "text")} className="label">
                What needs doing
              </label>
              <div className="flex gap-2">
                <input id={fid(i, "text")} className="input" maxLength={300} value={it.text} onChange={(e) => update(i, { text: e.target.value })} {...desc(i, "text")} />
                <button
                  type="button"
                  aria-label={`Remove action item ${i + 1}`}
                  className="btn-ghost shrink-0 text-red-700"
                  onClick={() => onChange(items.filter((_, j) => j !== i))}
                >
                  <Trash2 aria-hidden size={18} />
                </button>
              </div>
              {msg(i, "text")}
              {msg(i, "due_date")}
            </div>
          </div>
        </fieldset>
      ))}
      {items.length < max ? (
        <button type="button" className="btn-secondary" onClick={onAdd} disabled={students.length === 0}>
          <Plus aria-hidden size={16} /> Add action item
        </button>
      ) : null}
    </div>
  );
}
