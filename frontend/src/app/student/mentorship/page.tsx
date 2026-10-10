"use client";
// SCR-05 My mentorship (FLOW-08, REQ-009, REQ-010, REQ-014, REQ-024): everything the student sees about their mentoring.
// Session notes are never in this payload (REQ-015); issue text appears only when the server sends it.
import Link from "next/link";
import { useState } from "react";
import { CalendarClock, CheckCircle2, MessageSquarePlus, TriangleAlert } from "lucide-react";
import { SessionFeedback } from "@/components/student/SessionFeedback";
import { Dialog, EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill, useToast } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

type MyMentorship = components["schemas"]["MyMentorship"];
type SessionSummary = components["schemas"]["SessionSummary"];
type ActionItem = components["schemas"]["ActionItem"];
type Category = components["schemas"]["TopicCategory"];

const CATEGORIES: { value: Category; label: string }[] = [
  { value: "academic", label: "Academic" },
  { value: "attendance", label: "Attendance" },
  { value: "career", label: "Career" },
  { value: "research", label: "Research" },
  { value: "personal", label: "Personal" },
  { value: "other", label: "Other" },
];

function describeSession(s: SessionSummary): string {
  const topics = s.topics.join(", ");
  return `${formatDate(s.date)} · ${s.kind} · ${s.mode === "online" ? "online" : "in person"}${topics ? ` · ${topics}` : ""}`;
}

export default function MyMentorshipPage() {
  const toast = useToast();
  const { data, error, loading, reload } = useApi<MyMentorship>("/me/mentorship");
  const [busy, setBusy] = useState<string | null>(null);
  const [rating, setRating] = useState<string | null>(null); // session whose feedback form is open
  const [meeting, setMeeting] = useState(false);
  const [issue, setIssue] = useState(false);
  const [message, setMessage] = useState("");
  const [category, setCategory] = useState<Category>("academic");
  const [text, setText] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function confirmSession(s: SessionSummary) {
    setBusy(s.id);
    try {
      await api.post(`/sessions/${s.id}/confirm`);
      toast.success("Thanks, your attendance is confirmed");
      setRating(s.id); // B6: offer feedback right after a successful confirm
    } catch (e) {
      toast.error(isApiError(e) && e.code === "NOT_PRESENT" ? "You were marked absent for this session." : "Couldn't confirm. Try again.");
    } finally {
      setBusy(null);
      await reload();
    }
  }

  async function markDone(item: ActionItem) {
    setBusy(item.id);
    try {
      await api.patch(`/action-items/${item.id}`, { status: "done" });
      toast.success("Marked done. Your mentor will verify it.");
    } catch {
      toast.error("Couldn't update. Try again.");
    } finally {
      setBusy(null);
      await reload();
    }
  }

  async function sendMeeting() {
    const body = message.trim();
    if (!body) return setFormError("Write a short message.");
    setBusy("meeting");
    try {
      await api.post("/me/meeting-requests", { message: body });
      toast.success(`${data?.assigned_mentor?.name ?? "Your mentor"} has been notified.`);
      setMeeting(false);
      setMessage("");
      setFormError(null);
    } catch (e) {
      setFormError(isApiError(e) && e.status === 404 ? "You don't have a mentor yet." : "Couldn't send. Try again.");
    } finally {
      setBusy(null);
    }
  }

  async function raiseIssue() {
    const body = text.trim();
    const me = getSession();
    if (!body) return setFormError("Describe the problem.");
    if (!me) return;
    setBusy("issue");
    try {
      await api.post("/issues", { student_id: me.userId, category, text: body });
      toast.success("Your mentor has been told.");
      setIssue(false);
      setText("");
      setFormError(null);
      await reload();
    } catch {
      setFormError("Couldn't send. Try again.");
    } finally {
      setBusy(null);
    }
  }

  if (loading) {
    return (
      <>
        <PageHeader title="My mentorship" />
        <LoadingRegion label="Loading your mentorship">
          <div className="space-y-3">
            <Skeleton block />
            <Skeleton block />
          </div>
        </LoadingRegion>
      </>
    );
  }
  if (error || !data) {
    return (
      <>
        <PageHeader title="My mentorship" />
        {error ? <ErrorState error={error} onRetry={reload} homeHref="/student" /> : null}
      </>
    );
  }

  const openItems = data.action_items.filter((i) => i.status === "open");
  const waiting = data.action_items.filter((i) => i.status === "done");
  const closed = data.action_items.filter((i) => i.status === "verified" || i.status === "dropped");
  const mentor = data.assigned_mentor;

  return (
    <>
      <PageHeader
        title="My mentorship"
        actions={
          mentor ? (
            <>
              <button type="button" className="btn-secondary" onClick={() => { setFormError(null); setMeeting(true); }}>
                <CalendarClock aria-hidden size={16} /> Request a meeting
              </button>
              <button type="button" className="btn-secondary" onClick={() => { setFormError(null); setIssue(true); }}>
                <MessageSquarePlus aria-hidden size={16} /> Raise an issue
              </button>
            </>
          ) : undefined
        }
      />
      <div className="space-y-8">
        <section aria-labelledby="mentor-title" className="card space-y-2">
          <h2 id="mentor-title" className="section-title">
            Assigned mentor
          </h2>
          {mentor ? (
            <>
              {/* B7 REQ-035: the mentor's name opens their track record. */}
              <Link href={`/faculty-profile/${mentor.user_id}`} className="text-lg font-black text-brand underline underline-offset-2">
                {mentor.name}
              </Link>
              <p className="text-sm text-gray-600">
                {mentor.designation} · <a className="font-bold text-brand underline" href={`mailto:${mentor.email}`}>{mentor.email}</a>
              </p>
            </>
          ) : (
            <p className="text-sm font-bold text-gray-700">No mentor assigned yet. Your HOD allots mentors.</p>
          )}
          <p className="text-sm text-gray-600">
            Next follow-up: <strong>{data.next_followup ? formatDate(data.next_followup) : "not scheduled"}</strong>
          </p>
          {data.guides.length > 0 ? (
            <p className="text-sm text-gray-600">
              Research guide{data.guides.length === 1 ? "" : "s"}:{" "}
              {data.guides.map((g, i) => (
                <span key={g.id}>
                  {i > 0 ? ", " : null}
                  <Link href={`/faculty-profile/${g.mentor.user_id}`} className="font-bold text-brand underline">
                    {g.mentor.name}
                  </Link>
                  {g.opening_title ? ` (${g.opening_title})` : null}
                </span>
              ))}
            </p>
          ) : null}
        </section>

        <section aria-labelledby="confirm-title" className="space-y-3">
          <h2 id="confirm-title" className="section-title">
            Sessions to confirm ({data.sessions_to_confirm.length})
          </h2>
          {data.sessions_to_confirm.length === 0 ? (
            <p className="text-sm text-gray-600">Nothing to confirm.</p>
          ) : (
            <ul className="space-y-2">
              {data.sessions_to_confirm.map((s) => (
                <li key={s.id} className="card flex flex-wrap items-center justify-between gap-3 p-4">
                  <div>
                    <p className="text-sm font-bold text-gray-900">{describeSession(s)}</p>
                    <p className="text-xs text-gray-600">Logged by {s.logged_by.name}</p>
                  </div>
                  <button type="button" className="btn-primary" disabled={busy === s.id} onClick={() => void confirmSession(s)}>
                    Confirm I attended
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="actions-title" className="space-y-3">
          <h2 id="actions-title" className="section-title">
            Action items
          </h2>
          {data.action_items.length === 0 ? (
            <p className="text-sm text-gray-600">No action items yet.</p>
          ) : (
            <div className="space-y-4">
              {openItems.length > 0 ? (
                <ul className="space-y-2">
                  {openItems.map((i) => (
                    <li key={i.id} className={`flex items-start gap-3 rounded-2xl border p-3 ${i.overdue ? "border-red-200 bg-red-50" : "border-gray-200 bg-white"}`}>
                      <input
                        id={`done-${i.id}`}
                        type="checkbox"
                        className="mt-1 h-5 w-5 accent-[#8c1515]"
                        checked={false}
                        disabled={busy === i.id}
                        onChange={() => void markDone(i)}
                      />
                      <label htmlFor={`done-${i.id}`} className="min-w-0 flex-1 cursor-pointer">
                        <span className="block text-sm font-bold text-gray-900">{i.text}</span>
                        <span className="text-xs text-gray-600">Due {formatDate(i.due_date)} · tick to mark done</span>
                      </label>
                      <StatusPill status={i.overdue ? "overdue" : "open"} />
                    </li>
                  ))}
                </ul>
              ) : null}
              {waiting.length > 0 ? (
                <div>
                  <h3 className="mb-2 text-xs font-black uppercase tracking-widest text-gray-600">Waiting for mentor ({waiting.length})</h3>
                  <ul className="space-y-2">
                    {waiting.map((i) => (
                      <li key={i.id} className="flex items-center justify-between gap-2 rounded-2xl border border-gray-200 bg-white p-3">
                        <span className="text-sm text-gray-800">{i.text}</span>
                        <StatusPill status="done" />
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {closed.length > 0 ? (
                <p className="text-xs text-gray-600">{closed.length} closed item{closed.length === 1 ? "" : "s"} (verified or dropped).</p>
              ) : null}
            </div>
          )}
        </section>

        <section aria-labelledby="issues-title" className="space-y-3">
          <h2 id="issues-title" className="section-title">
            Issues
          </h2>
          {data.issues.length === 0 ? (
            <p className="text-sm text-gray-600">No issues raised.</p>
          ) : (
            <ul className="space-y-2">
              {data.issues.map((i) => (
                <li key={i.id} className="card space-y-1 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-black capitalize text-gray-900">{i.category}</p>
                    <StatusPill status={i.status} />
                  </div>
                  <p className="text-xs text-gray-600">Raised {formatDate(i.raised_at)}</p>
                  {i.text ? <p className="text-sm text-gray-800">{i.text}</p> : null}
                  {i.resolution ? <p className="text-sm text-gray-700">Resolution: {i.resolution}</p> : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="applications-title" className="space-y-3">
          <h2 id="applications-title" className="section-title">
            Applications
          </h2>
          {data.applications.length === 0 ? (
            <EmptyState message="You haven't applied to any opening yet." action={<Link href="/student" className="btn-secondary">Browse openings</Link>} />
          ) : (
            <ul className="space-y-2">
              {data.applications.map((a) => (
                <li key={a.id} className="card flex flex-wrap items-center justify-between gap-2 p-4">
                  <Link href={`/student/openings/${a.opening_id}`} className="text-sm font-black text-gray-900 hover:underline">
                    {a.opening_title}
                  </Link>
                  <StatusPill status={a.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="recent-title" className="space-y-3">
          <h2 id="recent-title" className="section-title">
            Recent sessions
          </h2>
          {data.recent_sessions.length === 0 ? (
            <p className="text-sm text-gray-600">No sessions yet.</p>
          ) : (
            <ul className="space-y-2">
              {data.recent_sessions.map((s) => (
                <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-gray-200 bg-white p-3">
                  <span className="text-sm text-gray-800">{describeSession(s)}</span>
                  {!s.present ? (
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-gray-600">
                      <TriangleAlert aria-hidden size={14} /> Marked absent
                    </span>
                  ) : s.confirmed_at ? (
                    <span className="flex flex-wrap items-center gap-3">
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-green-800">
                        <CheckCircle2 aria-hidden size={14} /> Confirmed
                      </span>
                      <button
                        type="button"
                        className="text-xs font-bold text-brand underline"
                        aria-expanded={rating === s.id}
                        onClick={() => setRating(rating === s.id ? null : s.id)}
                      >
                        {rating === s.id ? "Hide feedback" : "Rate this session"}
                      </button>
                    </span>
                  ) : (
                    <StatusPill status="unconfirmed" />
                  )}
                  {/* Absent attendees never get the buttons (the API answers 409 NOT_PRESENT anyway). */}
                  {s.present && s.confirmed_at && rating === s.id ? <SessionFeedback sessionId={s.id} label={formatDate(s.date)} /> : null}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <Dialog
        open={meeting}
        onClose={() => setMeeting(false)}
        size="sm"
        title="Request a meeting"
        description={mentor ? `${mentor.name} will be notified with your message.` : undefined}
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={() => setMeeting(false)}>
              Cancel
            </button>
            <button type="button" className="btn-primary" disabled={busy === "meeting"} onClick={() => void sendMeeting()}>
              Send
            </button>
          </>
        }
      >
        <label htmlFor="meeting-message" className="label">
          Message (up to 300 characters)
        </label>
        <textarea id="meeting-message" className="input" rows={4} maxLength={300} value={message} onChange={(e) => setMessage(e.target.value)} />
        {formError ? <p role="alert" className="mt-1 text-xs font-bold text-red-700">{formError}</p> : null}
      </Dialog>

      <Dialog
        open={issue}
        onClose={() => setIssue(false)}
        size="sm"
        title="Raise an issue"
        description="Your mentor will see this. It is not shared with the department as text."
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={() => setIssue(false)}>
              Cancel
            </button>
            <button type="button" className="btn-primary" disabled={busy === "issue"} onClick={() => void raiseIssue()}>
              Send
            </button>
          </>
        }
      >
        <label htmlFor="issue-category" className="label">
          Category
        </label>
        <select id="issue-category" className="input" value={category} onChange={(e) => setCategory(e.target.value as Category)}>
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <label htmlFor="issue-text" className="label mt-3">
          What is the problem? (up to 1000 characters)
        </label>
        <textarea id="issue-text" className="input" rows={4} maxLength={1000} value={text} onChange={(e) => setText(e.target.value)} />
        {formError ? <p role="alert" className="mt-1 text-xs font-bold text-red-700">{formError}</p> : null}
      </Dialog>
    </>
  );
}
