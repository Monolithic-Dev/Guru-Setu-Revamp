"use client";
// Component gallery for T1.P3.4 "Done when". Removed in Phase 6 (T6.P3.3).
import { useState } from "react";
import {
  AttentionBadge,
  Avatar,
  Dialog,
  EmptyState,
  ErrorState,
  ExportButton,
  KpiTile,
  PageHeader,
  SkillChip,
  Skeleton,
  StatusPill,
  Timeline,
  TrustBadge,
  useToast,
} from "@/components/ui";

const STATUSES = [
  "processing", "certified", "needs_review", "duplicate", "failed", "rejected",
  "pending", "shortlisted", "accepted", "completed",
  "open", "overdue", "done", "verified", "dropped",
  "raised", "acknowledged", "in_progress", "resolved", "confirmed", "unconfirmed", "draft", "sample",
];

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card space-y-3">
      <h2 className="section-title">{title}</h2>
      {children}
    </section>
  );
}

export default function ComponentGallery() {
  const [open, setOpen] = useState(false);
  const toast = useToast();

  return (
    <main className="mx-auto max-w-5xl space-y-6 bg-canvas p-6">
      <PageHeader title="Component gallery" subtitle="Dev only (T1.P3.4). Removed before the demo." backHref="/" />

      <Block title="Buttons">
        <div className="flex flex-wrap gap-3">
          <button type="button" className="btn-primary">Primary</button>
          <button type="button" className="btn-secondary">Secondary</button>
          <button type="button" className="btn-ghost">Ghost</button>
          <button type="button" className="btn-primary" disabled>Disabled</button>
          <ExportButton href="/evidence/mentoring.xlsx" filename="gurusetu-mentoring-DRAFT.xlsx" label="Export mentoring pack" />
        </div>
      </Block>

      <Block title="Status pills">
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <StatusPill key={s} status={s} />
          ))}
          <StatusPill status="pending" label="Applied · Pending" />
        </div>
      </Block>

      <Block title="Trust badges and skill chips">
        <div className="flex flex-wrap gap-2">
          <TrustBadge level={0} />
          <TrustBadge level={1} source="Deep Learning with PyTorch" />
          <TrustBadge level={2} source="Dr. Meera Raman" />
        </div>
        <div className="flex flex-wrap gap-2">
          <SkillChip concept="python" kind="matched" trustLevel={1} source="Python for Everybody" />
          <SkillChip concept="pytorch" kind="claimed_only" trustLevel={0} proveHref="/student/certificates" />
          <SkillChip concept="computer vision" kind="near" via="deep learning" />
          <SkillChip concept="embedded c" kind="missing" proveHref="/student/certificates" />
          <SkillChip concept="pytorch" kind="matched" trustLevel={2} />
        </div>
      </Block>

      <Block title="Attention badges">
        <div className="flex flex-wrap gap-2">
          <AttentionBadge reason="no_recent_session" />
          <AttentionBadge reason="no_meeting_this_term" />
          <AttentionBadge reason="overdue_action" />
          <AttentionBadge reason="stale_issue" />
          <AttentionBadge reason="marked_at_risk" />
          <AttentionBadge reason="suggested_at_risk" detail="attendance 68%" />
        </div>
      </Block>

      <Block title="KPI tiles">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <KpiTile label="Allotted" value="48/50" sub="2 unallotted" />
          <KpiTile label="Ratio" value="1:12" />
          <KpiTile label="Compliance" value="91.7%" highlight />
          <KpiTile label="Issues resolved" value="11/13" href="/coordinator/metrics/issues_resolved" />
        </div>
      </Block>

      <Block title="Avatars">
        <div className="flex items-center gap-3">
          <Avatar name="Dr. Meera Raman" size="sm" />
          <Avatar name="Aarav Menon" />
          <Avatar name="Karthik S" size="lg" />
          <span className="rounded-full bg-brand p-2">
            <Avatar name="Suresh Iyer" inverted />
          </span>
        </div>
      </Block>

      <Block title="Timeline">
        <Timeline
          events={[
            { id: "1", date: "2026-10-10", title: "Group session (12 present)", kind: "session" },
            { id: "2", date: "2026-10-07", title: "Share updated resume", detail: "Overdue", kind: "action" },
            { id: "3", date: "2026-09-20", title: "Attendance issue raised", kind: "issue" },
            { id: "4", date: "2026-09-01", title: "Application pending → shortlisted", kind: "status" },
          ]}
        />
      </Block>

      <Block title="States">
        <Skeleton />
        <Skeleton block />
        <EmptyState message="No certificates yet. Upload one to turn claimed skills into Certified." />
        <ErrorState error={{ status: 500, code: "INTERNAL", errors: [], requestId: "req-4f2a" }} onRetry={() => toast.show("Retry pressed")} />
        <ErrorState error={{ status: 404, code: "NOT_FOUND", errors: [] }} />
        <ErrorState error={{ status: 403, code: "FORBIDDEN", errors: [] }} />
        <ErrorState inline error={{ status: 503, code: "DB_UNAVAILABLE", errors: [] }} onRetry={() => undefined} />
      </Block>

      <Block title="Toasts and dialog">
        <div className="flex flex-wrap gap-3">
          <button type="button" className="btn-secondary" onClick={() => toast.success("Session saved for 12 students")}>
            Success toast
          </button>
          <button type="button" className="btn-secondary" onClick={() => toast.error("Couldn't update. Try again.")}>
            Error toast
          </button>
          <button type="button" className="btn-secondary" onClick={() => toast.show("This application changed. Refreshing.")}>
            Info toast
          </button>
          <button type="button" className="btn-primary" onClick={() => setOpen(true)}>
            Open dialog
          </button>
        </div>
        <Dialog
          open={open}
          onClose={() => setOpen(false)}
          title="Reject certificate"
          description="Give a reason (at least 3 characters)."
          footer={
            <>
              <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
              <button type="button" className="btn-primary" onClick={() => setOpen(false)}>Reject</button>
            </>
          }
        >
          <label htmlFor="reason" className="label">Reason</label>
          <textarea id="reason" className="input" rows={3} />
        </Dialog>
      </Block>
    </main>
  );
}
