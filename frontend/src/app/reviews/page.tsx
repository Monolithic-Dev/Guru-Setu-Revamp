"use client";
// SCR-10 Certificate review queue (FLOW-05, REQ-002): approve, or reject with a reason; 409 means someone else got there first.
import { useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { ReviewCard } from "@/components/mentor/ReviewCard";
import { Dialog, EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, useToast } from "@/components/ui";
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type ReviewItem = components["schemas"]["ReviewItem"];
type ReviewDecision = components["schemas"]["ReviewDecision"];

export default function ReviewsPage() {
  const toast = useToast();
  const { data, error, loading, reload, setData } = useApi<ReviewItem[]>("/reviews/certificates", { fixture: fixtures.reviewQueue });
  const [busyId, setBusyId] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<ReviewItem | null>(null);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);

  const remove = (id: string) => setData((data ?? []).filter((i) => i.certificate.id !== id));

  async function decide(item: ReviewItem, body: ReviewDecision): Promise<boolean> {
    const id = item.certificate.id;
    setBusyId(id);
    try {
      await api.post(`/certificates/${id}/review`, body);
      remove(id);
      toast.success(body.decision === "approve" ? "Approved" : "Rejected");
      return true;
    } catch (e) {
      if (isApiError(e) && e.code === "ALREADY_REVIEWED") {
        remove(id);
        toast.show("Already reviewed by someone else.");
        return true;
      }
      if (isApiError(e) && e.status === 422 && body.decision === "reject") {
        setReasonError(e.errors[0]?.message ?? "Give a reason (at least 3 characters).");
        return false;
      }
      toast.error("Couldn't save the review. Try again.");
      return false;
    } finally {
      setBusyId(null);
    }
  }

  async function submitReject() {
    if (!rejecting) return;
    const text = reason.trim();
    if (text.length < 3 || text.length > 300) {
      setReasonError("Give a reason (at least 3 characters).");
      document.getElementById("reject-reason")?.focus();
      return;
    }
    if (await decide(rejecting, { decision: "reject", reason: text })) closeReject();
  }

  function closeReject() {
    setRejecting(null);
    setReason("");
    setReasonError(null);
  }

  return (
    <>
      <PageHeader
        title="Certificate reviews"
        subtitle={data ? `${data.length} waiting for a decision` : "Certificates that need a person to check them."}
      />
      {loading ? (
        <LoadingRegion label="Loading review queue">
          <div className="space-y-3">
            <Skeleton block />
            <Skeleton block />
          </div>
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : !data || data.length === 0 ? (
        <EmptyState icon={<ClipboardCheck size={36} />} message="Nothing to review right now." />
      ) : (
        <ul className="space-y-4">
          {data.map((item) => (
            <li key={item.certificate.id}>
              <ReviewCard
                item={item}
                busy={busyId === item.certificate.id}
                onApprove={(i) => void decide(i, { decision: "approve" })}
                onReject={(i) => setRejecting(i)}
              />
            </li>
          ))}
        </ul>
      )}

      <Dialog
        open={rejecting !== null}
        onClose={closeReject}
        size="sm"
        title="Reject certificate"
        description="Only the student and reviewers see this reason."
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={closeReject}>
              Cancel
            </button>
            <button type="button" className="btn-primary" onClick={() => void submitReject()} disabled={busyId !== null}>
              Reject
            </button>
          </>
        }
      >
        <label htmlFor="reject-reason" className="label">
          Reason
        </label>
        <textarea
          id="reject-reason"
          className="input"
          rows={3}
          maxLength={300}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          aria-invalid={!!reasonError}
          aria-describedby={reasonError ? "reject-reason-error" : "reject-reason-count"}
        />
        <p id="reject-reason-count" className="mt-1 text-right text-xs text-gray-600">
          {reason.length}/300
        </p>
        {reasonError ? (
          <p id="reject-reason-error" role="alert" className="text-xs font-bold text-red-700">
            {reasonError}
          </p>
        ) : null}
      </Dialog>
    </>
  );
}
