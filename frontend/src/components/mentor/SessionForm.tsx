"use client";
// Session log (FLOW-07; REQ-008, 010, 011; NFR-03 ≤ 120 s). Field order and defaults follow ux-flows §3;
// validation copy follows ux-flows §6. One Idempotency-Key per form, reused on Retry (FM-04).
import { useMemo, useRef, useState, type FormEvent } from "react";
import { Lock, RefreshCw, Save } from "lucide-react";
import { Segmented, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { addDays, todayIst } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";
import { ActionItemEditor, type ActionDraft } from "./ActionItemEditor";
import { AttendeePicker, type AttendeeSelection } from "./AttendeePicker";
import { IssueEditor, type IssueDraft } from "./IssueEditor";
import { TopicChips, type Topic } from "./TopicChips";

type MenteeRow = components["schemas"]["MenteeRow"];
type OpeningSummary = components["schemas"]["OpeningSummary"];
type SessionCreate = components["schemas"]["SessionCreate"];
type SessionDetail = components["schemas"]["SessionDetail"];

export interface SessionFormProps {
  rows: MenteeRow[];
  /** The faculty member's own openings, for the research-guide context. */
  openings: OpeningSummary[];
  /** Pre-fills an individual session for one student (from Mentee 360). */
  prefillStudentId?: string | null;
  onSaved: (session: SessionDetail, presentCount: number) => void;
  onCancel: () => void;
}

const MAX_ATTENDEES = 40;
let keySeq = 0;
const newKey = () => `k${++keySeq}`;

/** Server field path ("action_items[1].text") → form error key ("actions.1.text"). */
function mapServerField(field: string): string {
  const m = /^(action_items|issues|attendees)\[(\d+)\]\.?(\w+)?$/.exec(field);
  if (m) {
    if (m[1] === "attendees") return "attendees";
    const base = m[1] === "action_items" ? "actions" : "issues";
    return `${base}.${m[2]}.${m[3] ?? "text"}`;
  }
  return field.split(/[.[]/)[0];
}

const domId = (key: string) => `sf-${key.replace(/\./g, "-")}`;

export function SessionForm({ rows, openings, prefillStudentId, onSaved, onCancel }: SessionFormProps) {
  const toast = useToast();
  const today = todayIst();
  const idempotencyKey = useRef<string>(typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);

  const [date, setDate] = useState(today);
  const [mode, setMode] = useState<SessionCreate["mode"]>("in_person");
  const [kind, setKind] = useState<SessionCreate["kind"]>(prefillStudentId ? "individual" : "group");
  const prefillRow = rows.find((r) => r.student_id === prefillStudentId);
  const [context, setContext] = useState<SessionCreate["context"]>(prefillRow?.mentorship_type === "guide" ? "guide" : "assigned");
  const [openingId, setOpeningId] = useState<string>("");
  const [selected, setSelected] = useState<AttendeeSelection>(prefillStudentId ? { [prefillStudentId]: { present: true } } : {});
  const [topics, setTopics] = useState<Topic[]>([]);
  const [notes, setNotes] = useState("");
  const [followup, setFollowup] = useState("");
  const [actions, setActions] = useState<ActionDraft[]>([]);
  const [issues, setIssues] = useState<IssueDraft[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [canRetry, setCanRetry] = useState(false);

  const visibleRows = useMemo(() => rows.filter((r) => r.mentorship_type === context), [rows, context]);
  const selectedStudents = useMemo(
    () => visibleRows.filter((r) => selected[r.student_id]).map((r) => ({ id: r.student_id, name: r.name })),
    [visibleRows, selected],
  );
  const presentCount = selectedStudents.filter((s) => selected[s.id]?.present).length;

  /** Clear errors whose key equals `key` or starts with `key.` once the user edits that field. */
  function clear(...keys: string[]) {
    setErrors((cur) => {
      const hit = Object.keys(cur).filter((k) => keys.some((key) => k === key || k.startsWith(`${key}.`)));
      if (hit.length === 0) return cur;
      const next = { ...cur };
      hit.forEach((k) => delete next[k]);
      return next;
    });
  }

  function changeContext(next: SessionCreate["context"]) {
    setContext(next);
    setSelected({});
    setActions([]);
    setIssues([]);
  }

  function changeKind(next: SessionCreate["kind"]) {
    setKind(next);
    if (next === "individual" && selectedStudents.length > 1) {
      const first = selectedStudents[0].id;
      setSelected({ [first]: selected[first] });
    }
  }

  function validate(): Record<string, string> {
    const e: Record<string, string> = {};
    if (!date) e.date = "This field is required.";
    else if (date > today) e.date = "Session date cannot be in the future.";
    if (context === "guide" && !openingId) e.opening_id = "Choose the opening this session is about.";
    if (selectedStudents.length === 0) e.attendees = "Select at least one student.";
    else if (kind === "individual" && selectedStudents.length !== 1) e.attendees = "An individual session has one student.";
    else if (selectedStudents.length > MAX_ATTENDEES) e.attendees = `Select at most ${MAX_ATTENDEES} students.`;
    if (topics.length === 0) e.topics = "Pick at least one topic.";
    const ids = new Set(selectedStudents.map((s) => s.id));
    actions.forEach((a, i) => {
      if (!a.student_id || !ids.has(a.student_id)) e[`actions.${i}.student_id`] = "Choose a student from the attendees.";
      if (!a.text.trim()) e[`actions.${i}.text`] = "This field is required.";
      else if (a.text.length > 300) e[`actions.${i}.text`] = "Keep action items under 300 characters.";
      if (!a.due_date) e[`actions.${i}.due_date`] = "This field is required.";
      else if (date && a.due_date < date) e[`actions.${i}.due_date`] = "Due date must be on or after the session date.";
    });
    issues.forEach((it, i) => {
      if (!it.student_id || !ids.has(it.student_id)) e[`issues.${i}.student_id`] = "Choose a student from the attendees.";
      if (!it.text.trim()) e[`issues.${i}.text`] = "This field is required.";
    });
    if (followup && date && followup <= date) e.next_followup = "Follow-up must be after the session date.";
    return e;
  }

  function focusFirst(errs: Record<string, string>) {
    const order = ["date", "opening_id", "attendees", "topics", "notes"];
    const keys = Object.keys(errs).sort((a, b) => {
      const ia = order.indexOf(a) === -1 ? 50 : order.indexOf(a);
      const ib = order.indexOf(b) === -1 ? 50 : order.indexOf(b);
      return ia - ib;
    });
    if (keys[0]) document.getElementById(domId(keys[0]))?.focus();
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length) return focusFirst(errs);

    const body: SessionCreate = {
      date,
      mode,
      kind,
      context,
      opening_id: context === "guide" ? openingId : null,
      attendees: selectedStudents.map((s) => ({ student_id: s.id, present: selected[s.id].present })),
      topics,
      notes: notes.trim() ? notes : null,
      confidential: false,
      next_followup: followup || null,
      action_items: actions.map(({ student_id, text, owner, due_date }) => ({ student_id, text: text.trim(), owner, due_date })),
      issues: issues.map(({ student_id, category, text }) => ({ student_id, category, text: text.trim(), confidential: false })),
    };

    setBusy(true);
    setCanRetry(false);
    try {
      const { data } = await api.post<SessionDetail>("/sessions", body, { headers: { "Idempotency-Key": idempotencyKey.current } });
      onSaved(data, presentCount);
    } catch (err) {
      if (!isApiError(err)) {
        setFormError("Something went wrong. Try again.");
      } else if (err.status === 0) {
        setFormError("Couldn't reach the server. Your session is not saved yet.");
        setCanRetry(true);
      } else if (err.status === 422) {
        const mapped: Record<string, string> = {};
        err.errors.forEach((fe) => (mapped[mapServerField(fe.field)] ??= fe.message));
        if (err.code === "NOT_YOUR_MENTEE" && !mapped.attendees) mapped.attendees = err.detail ?? "One of the students is not your mentee.";
        if (Object.keys(mapped).length === 0) setFormError(err.detail ?? "Some details need fixing.");
        setErrors(mapped);
        focusFirst(mapped);
      } else {
        setFormError(err.status >= 500 ? "Something went wrong. Try again." : err.detail ?? "Couldn't save the session.");
        setCanRetry(err.status >= 500);
        if (err.requestId) toast.error(`Save failed (request ${err.requestId}).`);
      }
    } finally {
      setBusy(false);
    }
  }

  const fieldErr = (key: string) =>
    errors[key] ? (
      <p id={`${domId(key)}-error`} role="alert" className="mt-1 text-xs font-bold text-red-700">
        {errors[key]}
      </p>
    ) : null;
  const describe = (key: string) => (errors[key] ? { "aria-invalid": true, "aria-describedby": `${domId(key)}-error` } : {});

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      <section className="card space-y-4" aria-labelledby="sf-when">
        <h2 id="sf-when" className="section-title">
          When and how
        </h2>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="sf-date" className="label">
              Date
            </label>
            <input id="sf-date" type="date" max={today} className="input w-auto" value={date} onChange={(e) => {
                setDate(e.target.value);
                clear("date");
              }} {...describe("date")} />
            {fieldErr("date")}
          </div>
          <Segmented
            legend="Mode"
            value={mode}
            onChange={setMode}
            options={[
              { value: "in_person", label: "In person" },
              { value: "online", label: "Online" },
            ]}
          />
          <Segmented
            legend="Kind"
            value={kind}
            onChange={changeKind}
            options={[
              { value: "group", label: "Group" },
              { value: "individual", label: "Individual" },
            ]}
          />
        </div>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="sf-context" className="label">
              Context
            </label>
            <select id="sf-context" className="input w-auto" value={context} onChange={(e) => changeContext(e.target.value as SessionCreate["context"])}>
              <option value="assigned">Assigned mentees</option>
              <option value="guide">Research guide</option>
            </select>
          </div>
          {context === "guide" ? (
            <div className="min-w-[240px] flex-1">
              <label htmlFor="sf-opening_id" className="label">
                Opening
              </label>
              <select id="sf-opening_id" className="input" value={openingId} onChange={(e) => {
                  setOpeningId(e.target.value);
                  clear("opening_id");
                }} {...describe("opening_id")}>
                <option value="">Choose an opening</option>
                {openings.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.title}
                  </option>
                ))}
              </select>
              {fieldErr("opening_id")}
            </div>
          ) : null}
        </div>
      </section>

      <section className="card space-y-3" aria-labelledby="sf-attendees-title">
        <h2 id="sf-attendees-title" className="section-title">
          Attendees
        </h2>
        {visibleRows.length === 0 ? (
          <p className="text-sm text-gray-600">{context === "guide" ? "No guided students yet." : "No mentees assigned yet."}</p>
        ) : (
          <AttendeePicker
            id="sf-attendees"
            rows={visibleRows}
            value={selected}
            onChange={(v) => {
              setSelected(v);
              clear("attendees");
            }}
            single={kind === "individual"}
            selectAllLabel={context === "guide" ? "Select all guided students" : "Select all mentees"}
            describedBy={errors.attendees ? "sf-attendees-error" : undefined}
          />
        )}
        {fieldErr("attendees")}
      </section>

      <section className="card space-y-4" aria-labelledby="sf-discussed">
        <h2 id="sf-discussed" className="section-title">
          What was discussed
        </h2>
        <div>
          <p id="sf-topics-label" className="label">
            Topics
          </p>
          <TopicChips
            id="sf-topics"
            value={topics}
            onChange={(v) => {
              setTopics(v);
              clear("topics");
            }} labelledBy="sf-topics-label" describedBy={errors.topics ? "sf-topics-error" : undefined} />
          {fieldErr("topics")}
        </div>
        <div>
          <label htmlFor="sf-notes" className="label flex items-center gap-1">
            <Lock aria-hidden size={12} /> Notes (Private: only you can see this)
          </label>
          <textarea id="sf-notes" className="input" rows={3} maxLength={4000} value={notes} onChange={(e) => setNotes(e.target.value)} {...describe("notes")} />
          <p className="mt-1 text-right text-xs text-gray-600">{notes.length}/4000</p>
          {fieldErr("notes")}
        </div>
      </section>

      <section className="card space-y-3" aria-labelledby="sf-actions-title">
        <h2 id="sf-actions-title" className="section-title">
          Action items
        </h2>
        <ActionItemEditor
          items={actions}
          students={selectedStudents}
          errors={errors}
          onChange={(v) => {
            setActions(v);
            clear("actions");
          }}
          onAdd={() =>
            setActions((a) => [
              ...a,
              { key: newKey(), student_id: selectedStudents.length === 1 ? selectedStudents[0].id : "", text: "", owner: "mentee", due_date: addDays(date || today, 7) },
            ])
          }
        />
        {selectedStudents.length === 0 ? <p className="text-xs text-gray-600">Select attendees first to add action items or issues.</p> : null}
      </section>

      <section className="card space-y-3" aria-labelledby="sf-issues-title">
        <h2 id="sf-issues-title" className="section-title">
          Issues
        </h2>
        <IssueEditor
          items={issues}
          students={selectedStudents}
          errors={errors}
          onChange={(v) => {
            setIssues(v);
            clear("issues");
          }}
          onAdd={() =>
            setIssues((a) => [...a, { key: newKey(), student_id: selectedStudents.length === 1 ? selectedStudents[0].id : "", category: topics[0] ?? "academic", text: "" }])
          }
        />
      </section>

      <section className="card space-y-2" aria-labelledby="sf-next">
        <h2 id="sf-next" className="section-title">
          Next follow-up
        </h2>
        <label htmlFor="sf-next_followup" className="label">
          Date (optional)
        </label>
        <input id="sf-next_followup" type="date" min={date ? addDays(date, 1) : undefined} className="input w-auto" value={followup} onChange={(e) => {
            setFollowup(e.target.value);
            clear("next_followup");
          }} {...describe("next_followup")} />
        {fieldErr("next_followup")}
      </section>

      {formError ? (
        <p role="alert" className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-800">
          {formError}
        </p>
      ) : null}

      <div className="sticky bottom-20 z-20 flex flex-wrap items-center justify-between gap-3 rounded-card border border-gray-200 bg-white/95 p-4 shadow-lg backdrop-blur md:bottom-4">
        <p className="text-sm font-bold text-gray-700">
          {selectedStudents.length} selected · {presentCount} present
        </p>
        <div className="flex gap-2">
          <button type="button" className="btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={busy}>
            {canRetry ? <RefreshCw aria-hidden size={16} /> : <Save aria-hidden size={16} />}
            {busy ? "Saving…" : canRetry ? "Retry" : "Save session"}
          </button>
        </div>
      </div>
    </form>
  );
}
