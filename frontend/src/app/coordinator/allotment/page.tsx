"use client";
// SCR-12 Allotment (FLOW-06, REQ-007, REQ-028): unallotted students on the left, mentor load cards on the right.
// Assigning an overloaded mentor is allowed but flagged (backend §6.8). HOD only: IQAC gets a 403 and sees the notice.
import { useState } from "react";
import { UserPlus } from "lucide-react";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, useToast } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type AllotmentView = components["schemas"]["AllotmentView"];

const MAX_PER_REQUEST = 30; // API-023: 1 to 30 students per call

export default function AllotmentPage() {
  const toast = useToast();
  const { data, error, loading, reload, setData } = useApi<AllotmentView>("/dept/allotment");
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [mentorId, setMentorId] = useState("");
  const [busy, setBusy] = useState(false);

  function toggle(id: string) {
    setPicked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function assign() {
    const mentor = data?.mentors.find((m) => m.mentor_id === mentorId);
    if (!mentor || picked.size === 0) return;
    setBusy(true);
    try {
      const res = await api.post<AllotmentView>("/allotments", { mentor_id: mentorId, student_ids: Array.from(picked) });
      setData(res.data);
      toast.success(`${picked.size} student${picked.size === 1 ? "" : "s"} assigned to ${mentor.name}`);
      setPicked(new Set());
    } catch (e) {
      toast.error(isApiError(e) && e.status === 404 ? "That mentor or student was not found. Refreshing." : "Couldn't assign. Try again.");
      await reload();
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <>
        <PageHeader title="Allotment" />
        <LoadingRegion label="Loading allotment">
          <Skeleton block />
        </LoadingRegion>
      </>
    );
  }
  if (error || !data) {
    return (
      <>
        <PageHeader title="Allotment" />
        {error ? <ErrorState error={error} onRetry={reload} homeHref="/coordinator" /> : null}
      </>
    );
  }

  const chosen = data.mentors.find((m) => m.mentor_id === mentorId);
  const tooMany = picked.size > MAX_PER_REQUEST;

  return (
    <>
      <PageHeader title="Allotment" subtitle="Give every student an assigned mentor. Moving a student keeps the old link as history." backHref="/coordinator" backLabel="Dashboard" />
      <div className="grid gap-6 md:grid-cols-2">
        <section aria-labelledby="un-title" className="card space-y-3">
          <h2 id="un-title" className="section-title">
            Unallotted ({data.unallotted.length})
          </h2>
          {data.unallotted.length === 0 ? (
            <EmptyState message="Every student has a mentor." />
          ) : (
            <ul className="space-y-1">
              {data.unallotted.map((s) => (
                <li key={s.user_id}>
                  <label className="flex min-h-[44px] cursor-pointer items-center gap-3 rounded-xl px-2 hover:bg-gray-50">
                    <input type="checkbox" className="h-5 w-5 accent-[#8c1515]" checked={picked.has(s.user_id)} onChange={() => toggle(s.user_id)} />
                    <span className="text-sm font-bold text-gray-900">{s.name}</span>
                    <span className="text-xs text-gray-600">{s.roll_no} · Year {s.year}</span>
                  </label>
                  {s.suggested_mentor ? (
                    <p className="ml-10 flex flex-wrap items-center gap-2 pb-1 text-xs text-gray-600">
                      Suggested: <strong className="text-gray-800">{s.suggested_mentor.name}</strong> ({s.suggested_mentor.reason})
                      <button type="button" className="font-bold text-brand underline" onClick={() => { setMentorId(s.suggested_mentor?.mentor_id ?? ""); setPicked(new Set([s.user_id])); }}>
                        Use this
                      </button>
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="mentors-title" className="space-y-3">
          <h2 id="mentors-title" className="section-title">
            Mentors
          </h2>
          <ul className="space-y-2">
            {data.mentors.map((m) => (
              <li key={m.mentor_id} className="card flex items-center justify-between gap-3 p-4">
                <span className="text-sm font-black text-gray-900">{m.name}</span>
                <span className="flex items-center gap-2">
                  <span className="text-sm font-bold text-gray-800">{m.mentee_count} / 20</span>
                  {m.overloaded ? (
                    <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-black text-amber-900">
                      Overloaded ({m.mentee_count}/20)
                    </span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
          <div className="card space-y-3">
            <label htmlFor="mentor-select" className="label">
              Assign selected students to
            </label>
            <select id="mentor-select" className="input" value={mentorId} onChange={(e) => setMentorId(e.target.value)}>
              <option value="">Choose a mentor</option>
              {data.mentors.map((m) => (
                <option key={m.mentor_id} value={m.mentor_id}>
                  {m.name} ({m.mentee_count})
                </option>
              ))}
            </select>
            {tooMany ? <p role="alert" className="text-xs font-bold text-red-700">Select at most {MAX_PER_REQUEST} students at a time.</p> : null}
            <button type="button" className="btn-primary w-full" disabled={busy || picked.size === 0 || !chosen || tooMany} onClick={() => void assign()}>
              <UserPlus aria-hidden size={16} />
              {chosen && picked.size > 0 ? `Assign ${picked.size} student${picked.size === 1 ? "" : "s"} to ${chosen.name}` : "Assign"}
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
