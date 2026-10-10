"use client";
// Attendee list (FLOW-07): select mentees, then mark each present or absent (default present).
// For an individual session, picking a student replaces the previous pick.
import { AttentionBadge } from "@/components/ui";
import type { components } from "@/lib/types";

type MenteeRow = components["schemas"]["MenteeRow"];

export type AttendeeSelection = Record<string, { present: boolean }>;

export interface AttendeePickerProps {
  id?: string;
  rows: MenteeRow[];
  value: AttendeeSelection;
  onChange: (value: AttendeeSelection) => void;
  single?: boolean;
  /** Label for the select-all control, e.g. "Select all mentees". */
  selectAllLabel?: string;
  describedBy?: string;
}

export function AttendeePicker({ id, rows, value, onChange, single = false, selectAllLabel = "Select all mentees", describedBy }: AttendeePickerProps) {
  const selectedCount = rows.filter((r) => value[r.student_id]).length;
  const all = rows.length > 0 && selectedCount === rows.length;

  function toggle(sid: string) {
    if (value[sid]) {
      const next = { ...value };
      delete next[sid];
      onChange(next);
    } else {
      onChange(single ? { [sid]: { present: true } } : { ...value, [sid]: { present: true } });
    }
  }

  function toggleAll() {
    if (all) onChange({});
    else onChange(Object.fromEntries(rows.map((r) => [r.student_id, { present: value[r.student_id]?.present ?? true }])));
  }

  return (
    <div id={id} tabIndex={-1} aria-describedby={describedBy} className="outline-none">
      {!single && rows.length > 1 ? (
        <label className="mb-2 flex min-h-[44px] cursor-pointer items-center gap-3 rounded-xl bg-brand-tint px-3 text-sm font-black text-brand">
          <input
            type="checkbox"
            checked={all}
            ref={(el) => {
              if (el) el.indeterminate = selectedCount > 0 && !all;
            }}
            onChange={toggleAll}
            className="h-5 w-5 accent-brand"
          />
          {selectAllLabel} ({selectedCount}/{rows.length} selected)
        </label>
      ) : null}
      <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
        {rows.map((r) => {
          const sel = value[r.student_id];
          return (
            <li key={`${r.mentorship_type}-${r.student_id}`} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2">
              <label className="flex min-h-[44px] min-w-0 flex-1 cursor-pointer items-center gap-3">
                <input
                  type={single ? "radio" : "checkbox"}
                  name={single ? "attendee-single" : undefined}
                  checked={!!sel}
                  onChange={() => toggle(r.student_id)}
                  className="h-5 w-5 shrink-0 accent-brand"
                />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-bold text-gray-900">{r.name}</span>
                  <span className="flex flex-wrap items-center gap-1 text-xs text-gray-600">
                    {r.roll_no}
                    {r.attention_reasons.slice(0, 1).map((a) => (
                      <AttentionBadge key={a} reason={a} />
                    ))}
                  </span>
                </span>
              </label>
              <fieldset disabled={!sel} className="flex rounded-full bg-gray-100 p-1 disabled:opacity-40">
                <legend className="sr-only">Attendance for {r.name}</legend>
                {[true, false].map((present) => {
                  const pid = `att-${r.student_id}-${present ? "p" : "a"}`;
                  const on = sel ? sel.present === present : present;
                  return (
                    <span key={pid}>
                      <input
                        id={pid}
                        type="radio"
                        name={`att-${r.student_id}`}
                        checked={!!sel && on}
                        onChange={() => onChange({ ...value, [r.student_id]: { present } })}
                        className="peer sr-only"
                      />
                      <label
                        htmlFor={pid}
                        className={`inline-flex min-h-[36px] cursor-pointer items-center rounded-full px-3 text-xs font-black uppercase tracking-wide peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-brand ${
                          sel && on ? (present ? "bg-green-700 text-white" : "bg-gray-700 text-white") : "text-gray-600"
                        }`}
                      >
                        {present ? "Present" : "Absent"}
                      </label>
                    </span>
                  );
                })}
              </fieldset>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
