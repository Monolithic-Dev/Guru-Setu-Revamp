"use client";

/**
 * ScoreBreakdownBar - the three segments behind the score (AC-004.2). Owner: P1.
 *
 * The bar shows proportion; the legend below states each value as text. Colour
 * is never the only carrier of meaning, so the legend is not decoration - it is
 * the accessible version of the bar (NFR-05).
 *
 * The three components always sum to the score exactly (the scorer rounds each
 * one before summing), so the legend can be read as an explanation rather than
 * an approximation.
 */

import type { FitComponents } from "./types";

const SEGMENTS: {
  key: keyof FitComponents;
  label: string;
  bar: string;
  dot: string;
}[] = [
  {
    key: "semantic",
    label: "Profile match",
    bar: "bg-sky-500",
    dot: "bg-sky-500",
  },
  {
    key: "skill",
    label: "Verified skills",
    bar: "bg-emerald-500",
    dot: "bg-emerald-500",
  },
  {
    key: "concept",
    label: "Related skills",
    bar: "bg-violet-500",
    dot: "bg-violet-500",
  },
];

export interface ScoreBreakdownBarProps {
  components: FitComponents;
  score: number;
}

export function ScoreBreakdownBar({ components, score }: ScoreBreakdownBarProps) {
  // Widths are proportions of 100, not of the score: a 43.4 score should not
  // render as a full bar.
  const width = (value: number) => `${Math.max(0, Math.min(100, value))}%`;

  return (
    <div>
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-slate-200"
        role="img"
        aria-label={
          `Score ${score.toFixed(1)} of 100: ` +
          SEGMENTS.map((s) => `${s.label} ${components[s.key].toFixed(1)}`).join(", ")
        }
      >
        {SEGMENTS.map((segment) => (
          <div
            key={segment.key}
            className={segment.bar}
            style={{ width: width(components[segment.key]) }}
          />
        ))}
      </div>

      <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm">
        {SEGMENTS.map((segment) => (
          <div key={segment.key} className="flex items-center gap-2">
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${segment.dot}`}
              aria-hidden="true"
            />
            <dt className="text-slate-600">{segment.label}</dt>
            <dd className="font-medium tabular-nums text-slate-900">
              {components[segment.key].toFixed(1)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export default ScoreBreakdownBar;
