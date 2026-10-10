"use client";
// SCR-07 Mentee 360 (REQ-013): skills, academics [MOCK], one timeline, action items, issues, applications,
// certificates. Notes render only when the server sends them (REQ-015): no empty box otherwise.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Lock, Plus } from "lucide-react";
import { ActionItemList } from "@/components/mentor/ActionItemList";
import { EndorseButton } from "@/components/mentor/EndorseButton";
import { IssueList } from "@/components/mentor/IssueList";
import { LEVEL_LABEL, LearnerCard } from "@/components/mentor/LearnerCard";
import { TermSummary } from "@/components/mentor/TermSummary";
import {
  AttentionBadge,
  Avatar,
  ErrorState,
  LoadingRegion,
  PageHeader,
  Skeleton,
  StatusPill,
  Timeline,
  TrustBadge,
  type TimelineEvent,
} from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { firstName, formatDate, formatPct } from "@/lib/format";
import type { Role } from "@/lib/nav";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

// attention_details is sent on the overview too (same shape as MenteeRow), for the assigned mentor's own row.
type Overview = components["schemas"]["MenteeOverview"] & { attention_details?: Record<string, string> };
type SessionSummary = components["schemas"]["SessionSummary"];

const TOPIC: Record<string, string> = {
  academic: "Academic",
  attendance: "Attendance",
  career: "Career",
  research: "Research",
  personal: "Personal",
  other: "Other",
};

function SessionDetail({ s }: { s: SessionSummary }) {
  return (
    <div className="space-y-1">
      <p className="text-sm text-gray-700">
        {s.topics.map((t) => TOPIC[t] ?? t).join(", ")} · Logged by {s.logged_by.name}
        {s.context === "guide" ? " · Research guide" : ""}
      </p>
      <div className="flex flex-wrap gap-1">
        {s.present === false ? <StatusPill status="dropped" label="Absent" /> : null}
        {s.present !== false ? <StatusPill status={s.confirmed_at ? "confirmed" : "unconfirmed"} /> : null}
        {s.confidential ? <StatusPill status="draft" label="Confidential" /> : null}
      </div>
      {s.notes ? (
        <div className="mt-2 rounded-xl border border-brand-line bg-brand-tint p-3">
          <p className="mb-1 flex items-center gap-1 text-[11px] font-black uppercase tracking-widest text-brand">
            <Lock aria-hidden size={12} /> Private notes
          </p>
          <p className="whitespace-pre-wrap text-sm text-gray-900">{s.notes}</p>
        </div>
      ) : null}
    </div>
  );
}

function buildTimeline(o: Overview): TimelineEvent[] {
  const ev: TimelineEvent[] = [];
  o.sessions.forEach((s) =>
    ev.push({
      id: `s-${s.id}`,
      date: s.date,
      kind: "session",
      title: `${s.kind === "group" ? "Group" : "Individual"} session · ${s.mode === "online" ? "Online" : "In person"}`,
      detail: <SessionDetail s={s} />,
    }),
  );
  o.action_items.forEach((a) =>
    (a.history ?? []).forEach((h, i) =>
      ev.push({
        id: `a-${a.id}-${i}`,
        date: h.at,
        kind: "action",
        title: h.from_status ? `Action item ${h.from_status} → ${h.to_status}` : "Action item created",
        detail: `${a.text} · by ${h.actor_name}`,
      }),
    ),
  );
  o.issues.forEach((it) =>
    (it.history ?? []).forEach((h, i) =>
      ev.push({
        id: `i-${it.id}-${i}`,
        date: h.at,
        kind: "issue",
        title: h.from_status ? `${TOPIC[it.category] ?? it.category} issue ${h.from_status} → ${h.to_status.replace("_", " ")}` : `${TOPIC[it.category] ?? it.category} issue raised`,
        detail: `by ${h.actor_name}`,
      }),
    ),
  );
  o.applications.forEach((app) =>
    app.history.forEach((h, i) =>
      ev.push({
        id: `p-${app.id}-${i}`,
        date: h.at,
        kind: "application",
        title: h.from_status ? `Application ${h.from_status} → ${h.to_status}` : "Applied",
        detail: `${app.opening_title} · by ${h.actor_name}`,
      }),
    ),
  );
  o.certificates
    .filter((c) => c.status === "certified")
    .forEach((c) => ev.push({ id: `c-${c.id}`, date: c.updated_at, kind: "certificate", title: `Certificate verified: ${c.title ?? "Untitled"}` }));
  return ev;
}

function Section({ title, children, aside }: { title: string; children: React.ReactNode; aside?: React.ReactNode }) {
  const id = `sec-${title.toLowerCase().replace(/\W+/g, "-")}`;
  return (
    <section aria-labelledby={id} className="card space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h2 id={id} className="section-title">
          {title}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

export default function MenteeOverviewPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const [role, setRole] = useState<Role | null>(null);
  useEffect(() => setRole(getSession()?.role ?? null), []);
  const { data, error, loading, reload, setData } = useApi<Overview>(`/mentees/${studentId}/overview`);
  const events = useMemo(() => (data ? buildTimeline(data) : []), [data]);
  const isMentor = role === "faculty";
  const backHref = role === "hod" ? "/coordinator" : "/faculty";

  if (loading) {
    return (
      <LoadingRegion label="Loading mentee">
        <div className="space-y-3">
          <Skeleton lines={2} />
          <Skeleton block />
          <Skeleton block />
        </div>
      </LoadingRegion>
    );
  }
  if (error) return <ErrorState error={error} onRetry={reload} homeHref={backHref} />;
  if (!data) return null;

  const s = data.student;
  const mentors = data.mentorships.filter((m) => m.status === "active");

  return (
    <>
      <PageHeader
        backHref={backHref}
        backLabel={role === "hod" ? "Dashboard" : "My mentees"}
        title={s.name}
        subtitle={
          <span className="flex flex-wrap items-center gap-2">
            {s.roll_no} · Year {s.year} · {s.dept_code}
            {(data.attention_reasons ?? []).map((r) => (
              <AttentionBadge key={r} reason={r} detail={data.attention_details?.[r]} />
            ))}
          </span>
        }
        actions={
          isMentor ? (
            <Link href={`/faculty/sessions/new?student=${s.user_id}`} className="btn-primary">
              <Plus aria-hidden size={16} /> Log session for {firstName(s.name)}
            </Link>
          ) : null
        }
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-5">
          <Section title="Timeline">
            <Timeline events={events} emptyText="No sessions, actions or issues yet." />
          </Section>
          <Section title="Action items">
            <ActionItemList items={data.action_items} canEdit={isMentor} onChanged={() => void reload()} />
          </Section>
          <Section title="Issues">
            <IssueList
              issues={data.issues}
              isMentor={isMentor}
              canEdit={(issue) => isMentor || (role === "hod" && issue.escalated)}
              onChanged={() => void reload()}
            />
          </Section>
        </div>

        <div className="space-y-5">
          {/* REQ-029/033: the card exists only when the server sends the mentor-only fields. */}
          {isMentor && "learner_note" in data ? (
            <Section title="Learner">
              <LearnerCard studentId={s.user_id} level={data.learner_level} note={data.learner_note} atRisk={data.marked_at_risk} onSaved={setData} />
            </Section>
          ) : data.learner_level ? (
            <Section title="Learner">
              <p className="text-sm font-bold text-gray-900">{LEVEL_LABEL[data.learner_level]}</p>
            </Section>
          ) : null}

          {data.term_summary ? (
            <Section title="This term">
              <TermSummary summary={data.term_summary} />
            </Section>
          ) : null}

          <Section title="Mentors">
            {mentors.length === 0 ? (
              <p className="text-sm text-gray-600">No active mentor.</p>
            ) : (
              <ul className="space-y-2">
                {mentors.map((m) => (
                  <li key={m.id} className="flex items-center gap-3">
                    <Avatar name={m.mentor.name} size="sm" />
                    <span className="text-sm">
                      <span className="font-bold text-gray-900">{m.mentor.name}</span>
                      <span className="block text-xs text-gray-600">
                        {m.type === "assigned" ? "Assigned mentor" : `Research guide${m.opening_title ? ` · ${m.opening_title}` : ""}`} since {formatDate(m.since)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Skills">
            {s.skills.length === 0 ? (
              <p className="text-sm text-gray-600">No skills yet.</p>
            ) : (
              <ul className="space-y-2">
                {s.skills.map((k) => (
                  <li key={k.concept} className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-bold text-gray-900">{k.concept}</span>
                    <span className="flex flex-wrap items-center gap-1">
                      <TrustBadge level={k.trust_level} source={k.trust_level === 2 ? k.endorsed_by?.[0] : k.sources[0]?.title} />
                      {isMentor && k.trust_level < 2 ? (
                        <EndorseButton
                          studentId={s.user_id}
                          studentName={firstName(s.name)}
                          concept={k.concept}
                          onEndorsed={(profile) => setData({ ...data, student: profile })}
                        />
                      ) : null}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Academics" aside={<StatusPill status="sample" />}>
            {data.academics.length === 0 ? (
              <p className="text-sm text-gray-600">No academic records.</p>
            ) : (
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Academic snapshot (sample data)</caption>
                <thead>
                  <tr className="text-xs uppercase tracking-wider text-gray-600">
                    <th scope="col" className="pb-2">Term</th>
                    <th scope="col" className="pb-2">CGPA</th>
                    <th scope="col" className="pb-2">Attendance</th>
                    <th scope="col" className="pb-2">Backlogs</th>
                  </tr>
                </thead>
                <tbody>
                  {data.academics.map((a) => (
                    <tr key={a.term_id} className="border-t border-gray-100">
                      <td className="py-1.5 font-bold">{a.term_id}</td>
                      <td>{a.cgpa.toFixed(2)}</td>
                      <td className={a.attendance_pct < 75 ? "font-bold text-red-700" : ""}>{formatPct(a.attendance_pct)}</td>
                      <td>{a.backlogs}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Section>

          <Section title="Applications">
            {data.applications.length === 0 ? (
              <p className="text-sm text-gray-600">No applications.</p>
            ) : (
              <ul className="space-y-2">
                {data.applications.map((a) => (
                  <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span className="font-bold text-gray-900">{a.opening_title}</span>
                    <StatusPill status={a.status} />
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Certificates">
            {data.certificates.length === 0 ? (
              <p className="text-sm text-gray-600">No certificates.</p>
            ) : (
              <ul className="space-y-2">
                {data.certificates.map((c) => (
                  <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span className="min-w-0">
                      <span className="block font-bold text-gray-900">{c.kind === "project_record" ? `Project: ${c.title ?? "Guided work"}` : c.title ?? "Untitled certificate"}</span>
                      <span className="text-xs text-gray-600">{[c.issuer, c.issue_date ? formatDate(c.issue_date) : null].filter(Boolean).join(" · ")}</span>
                    </span>
                    <StatusPill status={c.status} />
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </div>
      </div>
    </>
  );
}
