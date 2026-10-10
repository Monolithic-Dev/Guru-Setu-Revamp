"use client";

/**
 * SCR-03 /student/openings/[id] - the explained Fit Check and Apply.
 * Owner: P1. Flow: FLOW-03. Endpoints: API-013, API-015, API-017, API-020.
 *
 * This is the screen the demo turns on: Aarav opens it at "Close", uploads four
 * certificates, comes back and it reads "Ready to apply" (index 7, steps 1-3).
 *
 * Reads go through P3's `useApi` and writes through P3's `api`, like every other
 * screen - a page never calls fetch or axios directly (ux-flows 8).
 */

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { EligibilityChecklist } from "@/components/profile/EligibilityChecklist";
import { FitPanel } from "@/components/fit/FitPanel";
import type { ApplicationStatus, Fit } from "@/components/fit/types";
import WhyGraph from "@/components/why/WhyGraph";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { features } from "@/lib/features";
import { isApiError } from "@/lib/problem";

interface OpeningDetail {
  id: string;
  title: string;
  description: string;
  faculty: { user_id: string; name: string };
  required_skills: string[];
  status: "open" | "closed";
}

const APPLY_LABEL: Record<ApplicationStatus, string> = {
  pending: "Applied · Pending",
  shortlisted: "Applied · Shortlisted",
  accepted: "Applied · Accepted",
  rejected: "Applied · Not selected",
  completed: "Applied · Completed",
};

export default function OpeningFitPage() {
  const params = useParams<{ id: string }>();
  const openingId = params?.id;

  const opening = useApi<OpeningDetail>(`/openings/${openingId}`);
  const fit = useApi<Fit>(`/openings/${openingId}/fit`);

  const [applied, setApplied] = useState<ApplicationStatus | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);
  const [showWhy, setShowWhy] = useState(false);

  async function apply() {
    setApplying(true);
    setApplyError(null);
    try {
      const response = await api.post<{ status: ApplicationStatus }>(
        `/openings/${openingId}/applications`,
        {},
      );
      setApplied(response.data?.status ?? "pending");
    } catch (err: unknown) {
      if (isApiError(err) && err.code === "ALREADY_APPLIED") {
        // Not an error from the student's point of view: they already applied,
        // so show the pill rather than a toast (FLOW-03 failure branch).
        setApplied("pending");
      } else if (isApiError(err) && err.code === "OPENING_CLOSED") {
        setApplyError(err.detail ?? "This opening is closed.");
      } else if (isApiError(err) && err.code === "NOT_ELIGIBLE") {
        setApplyError(`You can't apply yet. ${err.errors.map((e) => e.message).join(" ")}`);
      } else {
        setApplyError("We couldn't send your application. Please try again.");
      }
    } finally {
      setApplying(false);
    }
  }

  if (opening.loading || fit.loading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 p-4">
        <Skeleton lines={2} />
        <Skeleton block />
        <span className="sr-only">Loading the Fit Check</span>
      </div>
    );
  }

  const retry = () => {
    opening.reload();
    fit.reload();
  };

  const failure = opening.error ?? fit.error;
  if (failure) {
    return (
      <div className="mx-auto max-w-3xl p-4">
        <ErrorState error={failure} onRetry={retry} />
      </div>
    );
  }

  // No error but no payload either: treat it as empty rather than render a
  // half Fit Check.
  if (!opening.data || !fit.data) {
    return (
      <div className="mx-auto max-w-3xl p-4">
        <EmptyState message="This opening is no longer available." />
      </div>
    );
  }

  const closed = opening.data.status === "closed";

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4">
      <header>
        <h1 className="text-xl font-black text-gray-900">{opening.data.title}</h1>
        <p className="mt-1 text-sm text-gray-600">
          {/* B7 REQ-035: the faculty name opens their track record. */}
          <Link href={`/faculty-profile/${opening.data.faculty.user_id}`} className="font-bold text-brand underline underline-offset-2">
            {opening.data.faculty.name}
          </Link>
          {closed && " · Closed"}
        </p>
        {opening.data.description && (
          <p className="mt-3 text-sm text-gray-700">{opening.data.description}</p>
        )}
      </header>

      <EligibilityChecklist openingId={opening.data.id} />

      <div className="card">
        <FitPanel fit={fit.data} />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {applied ? (
          <span className="inline-flex min-h-[44px] items-center rounded-2xl bg-green-50 px-5 py-3 text-sm font-black uppercase tracking-widest text-green-900">
            {APPLY_LABEL[applied]}
          </span>
        ) : (
          <button
            type="button"
            onClick={() => void apply()}
            disabled={applying || closed}
            className="btn-primary"
          >
            {applying ? "Applying…" : "Apply"}
          </button>
        )}

        {features.whyGraph && (
          <button
            type="button"
            onClick={() => setShowWhy((shown) => !shown)}
            aria-expanded={showWhy}
            className="btn-secondary"
          >
            {showWhy ? "Hide why" : "Why?"}
          </button>
        )}
      </div>

      {applyError && (
        <p role="alert" className="text-sm font-bold text-red-700">
          {applyError}
        </p>
      )}

      {features.whyGraph && showWhy && <WhyGraph openingId={opening.data.id} />}
    </div>
  );
}
