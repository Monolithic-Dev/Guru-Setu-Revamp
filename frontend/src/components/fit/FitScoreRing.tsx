"use client";

/**
 * FitScoreRing - the score and verdict on SCR-03 (REQ-004). Owner: P1.
 *
 * The ring is decoration; the number and the verdict are text, so the value is
 * available to a screen reader and when CSS fails to load. The sweep animates
 * only when the viewer has not asked for reduced motion (NFR-05/06).
 */

import type { FitVerdict } from "./types";

const VERDICT_STYLES: Record<FitVerdict, { ring: string; text: string }> = {
  ready: { ring: "stroke-emerald-500", text: "text-emerald-700" },
  close: { ring: "stroke-amber-500", text: "text-amber-700" },
  not_yet: { ring: "stroke-slate-400", text: "text-slate-600" },
};

export interface FitScoreRingProps {
  score: number;
  verdict: FitVerdict;
  verdictText: string;
  /** Rendered smaller inside an applicant card on SCR-09. */
  compact?: boolean;
}

export function FitScoreRing({
  score,
  verdict,
  verdictText,
  compact = false,
}: FitScoreRingProps) {
  const size = compact ? 72 : 112;
  const stroke = compact ? 7 : 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);
  const styles = VERDICT_STYLES[verdict];

  return (
    <div className="flex items-center gap-4">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          aria-hidden="true"
          className="-rotate-90"
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            className="stroke-slate-200"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={`${styles.ring} transition-[stroke-dashoffset] duration-700 motion-reduce:transition-none`}
          />
        </svg>
        <span
          className={`absolute inset-0 flex items-center justify-center font-semibold tabular-nums ${
            compact ? "text-lg" : "text-2xl"
          } ${styles.text}`}
        >
          {clamped.toFixed(1)}
        </span>
      </div>

      <div>
        {/* The accessible name carries the number and the verdict together, so
            a screen reader does not have to stitch the ring and the label. */}
        <p className={`font-medium ${styles.text}`} role="status">
          <span className="sr-only">Fit score {clamped.toFixed(1)} out of 100. </span>
          {verdictText}
        </p>
        {!compact && (
          <p className="mt-1 text-sm text-slate-500">
            Out of 100
          </p>
        )}
      </div>
    </div>
  );
}

export default FitScoreRing;
