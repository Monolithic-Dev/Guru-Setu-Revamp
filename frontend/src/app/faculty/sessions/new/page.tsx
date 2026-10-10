"use client";
// SCR-08 Log a session (FLOW-07). Attendees come from API-024; `?student=<id>` pre-fills an individual session.
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { SessionForm } from "@/components/mentor/SessionForm";
import { ErrorState, LoadingRegion, PageHeader, Skeleton, useToast } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

type MenteeRow = components["schemas"]["MenteeRow"];
type OpeningSummary = components["schemas"]["OpeningSummary"];

function NewSession() {
  const router = useRouter();
  const params = useSearchParams();
  const toast = useToast();
  const student = params.get("student");
  const back = student ? `/faculty/mentees/${student}` : "/faculty";

  const [me, setMe] = useState<string | null>(null);
  useEffect(() => setMe(getSession()?.userId ?? null), []);

  const mentees = useApi<MenteeRow[]>("/me/mentees");
  const openings = useApi<OpeningSummary[]>("/openings");
  const ownOpenings = useMemo(() => (openings.data ?? []).filter((o) => o.faculty.user_id === me), [openings.data, me]);

  return (
    <>
      <PageHeader
        title="Log a session"
        subtitle="Attendance, topics, private notes, action items and issues in one save."
        backHref={back}
        backLabel={student ? "Back to mentee" : "My mentees"}
      />
      {mentees.loading ? (
        <LoadingRegion label="Loading mentees">
          <div className="space-y-3">
            <Skeleton block />
            <Skeleton block />
          </div>
        </LoadingRegion>
      ) : mentees.error ? (
        <ErrorState error={mentees.error} onRetry={mentees.reload} homeHref="/faculty" />
      ) : (
        <SessionForm
          rows={mentees.data ?? []}
          openings={ownOpenings}
          prefillStudentId={student}
          onCancel={() => router.push(back)}
          onSaved={(_session, present) => {
            toast.success(`Session saved for ${present} student${present === 1 ? "" : "s"}`);
            router.push(back);
          }}
        />
      )}
    </>
  );
}

export default function NewSessionPage() {
  return (
    <Suspense>
      <NewSession />
    </Suspense>
  );
}
