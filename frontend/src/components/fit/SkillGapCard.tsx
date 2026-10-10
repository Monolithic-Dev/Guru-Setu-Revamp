"use client";

/**
 * SkillGapCard - "learn X, unlock N openings" (API-021, REQ-021). Owner: P1.
 *
 * Rendered on SCR-02, which P4 owns, behind `features.skillGap`.
 *
 * openings_unlocked counts openings that would cross FIT_READY_MIN if the skill
 * were certified (ai-system §4). On the seed no single skill does that, so it
 * is often 0; the card then shows total_gain, which is the gain SUMMED over
 * every open opening that requires the skill - so it is worded as "across
 * openings", never as a gain on one opening.
 */

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { SkillGap } from "./types";

export interface SkillGapCardProps {
  gaps?: SkillGap[];
  loading?: boolean;
  certificatesHref?: string;
}

export function gapLabel(gap: SkillGap): string {
  if (gap.openings_unlocked > 0) {
    return `unlocks ${gap.openings_unlocked} ${gap.openings_unlocked === 1 ? "opening" : "openings"}`;
  }
  return `+${gap.total_gain.toFixed(1)} fit points across openings`;
}

export function SkillGapCard({
  gaps,
  loading = false,
  certificatesHref = "/student/certificates",
}: SkillGapCardProps) {
  // Nothing to say is better than an empty card.
  if (loading || !gaps || gaps.length === 0) return null;

  return (
    <section className="card space-y-3" aria-labelledby="skill-gap-heading">
      <h2 id="skill-gap-heading" className="section-title">
        Certify these to open more doors
      </h2>
      <ul className="divide-y divide-gray-100">
        {gaps.map((gap) => (
          <li key={gap.concept} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5 py-2">
            <span className="text-sm font-bold text-gray-900">{gap.concept}</span>
            <span className="text-sm text-gray-700">{gapLabel(gap)}</span>
          </li>
        ))}
      </ul>
      <Link href={certificatesHref} className="inline-flex items-center gap-1 text-sm font-bold text-brand underline underline-offset-2">
        Upload a certificate <ChevronRight aria-hidden size={14} />
      </Link>
    </section>
  );
}

export default SkillGapCard;
