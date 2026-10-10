"use client";

/**
 * SkillGapCard - "learn X, unlock N openings" (API-021, REQ-021). Owner: P1.
 *
 * Rendered on SCR-02, which P4 owns, behind `features.skillGap`. It is the
 * add-on A5 item: until that flag is flipped the host page renders it and it
 * returns null, so the seam exists from hour 7:30 without changing P4's file.
 */

import type { SkillGap } from "./types";

export interface SkillGapCardProps {
  gaps?: SkillGap[];
  loading?: boolean;
  certificatesHref?: string;
}

export function SkillGapCard({
  gaps,
  loading = false,
  certificatesHref = "/student/certificates",
}: SkillGapCardProps) {
  // Nothing to say is better than an empty card: a student with no gaps, or a
  // page rendering before the flag is on, shows nothing at all.
  if (loading || !gaps || gaps.length === 0) return null;

  return (
    <section
      className="rounded-lg border border-slate-200 p-4 dark:border-slate-700"
      aria-labelledby="skill-gap-heading"
    >
      <h2
        id="skill-gap-heading"
        className="text-sm font-semibold text-slate-900 dark:text-slate-100"
      >
        Certify these to open more doors
      </h2>
      <ul className="mt-3 space-y-2">
        {gaps.map((gap) => (
          <li key={gap.concept} className="flex items-baseline justify-between gap-3">
            <span className="text-sm text-slate-700 dark:text-slate-300">
              {gap.concept}
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {gap.openings_unlocked > 0
                ? `unlocks ${gap.openings_unlocked} ${
                    gap.openings_unlocked === 1 ? "opening" : "openings"
                  }`
                : `+${gap.total_gain.toFixed(1)} fit`}
            </span>
          </li>
        ))}
      </ul>
      <a
        href={certificatesHref}
        className="mt-3 inline-block text-sm font-medium text-sky-700 underline underline-offset-2 dark:text-sky-400"
      >
        Upload a certificate &rsaquo;
      </a>
    </section>
  );
}

export default SkillGapCard;
