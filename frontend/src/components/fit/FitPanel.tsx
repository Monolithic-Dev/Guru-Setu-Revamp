"use client";

/**
 * FitPanel - the whole explained Fit Check (REQ-004). Owner: P1.
 *
 * Used twice: on SCR-03 for the student, and read-only inside an applicant card
 * on SCR-09 (`readOnly`), so a faculty member sees exactly the explanation the
 * student saw. That is the point of the feature - the score is never a number
 * without a reason.
 *
 * Chips are grouped Matched / Claimed only / Near / Missing. The grouping is
 * the explanation: "claimed only" is what the student says, "matched" is what a
 * certificate proves, and keeping them apart is the whole trust argument.
 * The chips themselves are P3's `SkillChip`, so they look and read the same
 * here as on every other screen.
 */

import { SkillChip } from "@/components/ui/SkillChip";

import { FitScoreRing } from "./FitScoreRing";
import { ScoreBreakdownBar } from "./ScoreBreakdownBar";
import type { Fit, FitChip } from "./types";

const GROUPS: { kind: FitChip["kind"]; heading: string; hint?: string }[] = [
  { kind: "matched", heading: "Matched" },
  {
    kind: "claimed_only",
    heading: "Claimed only",
    hint: "You listed these. Upload a certificate to have them counted as verified.",
  },
  {
    kind: "near",
    heading: "Near",
    hint: "Counted partly, through a related skill you already have.",
  },
  { kind: "missing", heading: "Missing" },
];

export interface FitPanelProps {
  fit: Fit;
  /** Hides the student-only calls to action (used on SCR-09). */
  readOnly?: boolean;
  /** Where "Prove it" sends the student (SCR-04). */
  certificatesHref?: string;
}

export function FitPanel({
  fit,
  readOnly = false,
  certificatesHref = "/student/certificates",
}: FitPanelProps) {
  const grouped = GROUPS.map((group) => ({
    ...group,
    chips: fit.chips.filter((chip) => chip.kind === group.kind),
  })).filter((group) => group.chips.length > 0);

  return (
    <section className="space-y-6" aria-labelledby="fit-heading">
      <h2 id="fit-heading" className="sr-only">
        Fit Check
      </h2>

      <FitScoreRing
        score={fit.score}
        verdict={fit.verdict}
        verdictText={fit.verdict_text}
      />

      <ScoreBreakdownBar components={fit.components} score={fit.score} />

      {fit.note && (
        <p className="rounded-xl bg-gray-50 px-3 py-2 text-sm text-gray-600">
          {fit.note}
        </p>
      )}

      <div className="space-y-4">
        {grouped.map((group) => (
          <div key={group.kind}>
            <h3 className="section-title">{group.heading}</h3>
            {group.hint && (
              <p className="mt-1 text-xs text-gray-500">{group.hint}</p>
            )}
            <ul className="mt-2 flex flex-wrap gap-2">
              {group.chips.map((chip) => (
                <li key={`${group.kind}-${chip.concept}`}>
                  <SkillChip
                    concept={chip.concept}
                    kind={chip.kind}
                    trustLevel={chip.trust_level as 0 | 1 | 2 | null | undefined}
                    via={chip.via}
                    source={chip.source?.title}
                    // "Prove it" belongs only on the chips a certificate would
                    // change, and never on the faculty's read-only view.
                    proveHref={
                      !readOnly &&
                      (chip.kind === "claimed_only" || chip.kind === "missing")
                        ? certificatesHref
                        : undefined
                    }
                  />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {fit.gains.length > 0 && (
        <div>
          <h3 className="section-title">What would help most</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {fit.gains.map((gain) => (
              <li
                key={gain.concept}
                className="flex items-baseline justify-between gap-3 border-b border-gray-100 pb-1"
              >
                <span className="text-gray-700">Certify {gain.concept}</span>
                <span className="font-bold tabular-nums text-gray-900">
                  &rarr; {gain.score_if_certified.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

export default FitPanel;
