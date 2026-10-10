import Link from "next/link";
import { BadgeCheck, Circle, Minus, Waypoints } from "lucide-react";

export type SkillChipKind = "matched" | "claimed_only" | "near" | "missing";

// The chip text always includes its kind, so meaning never depends on colour (ux-flows §7).
const KIND = {
  matched: { word: "Certified", cls: "border-green-200 bg-green-50 text-green-900", Icon: BadgeCheck },
  claimed_only: { word: "Claimed", cls: "border-gray-300 bg-white text-gray-800", Icon: Circle },
  near: { word: "Near", cls: "border-gold-line bg-gold-soft text-gold-ink", Icon: Waypoints },
  missing: { word: "Missing", cls: "border-dashed border-gray-300 bg-gray-50 text-gray-700", Icon: Minus },
} as const;

export interface SkillChipProps {
  concept: string;
  kind: SkillChipKind;
  trustLevel?: 0 | 1 | 2 | null;
  /** For near matches: the held concept that is similar. */
  via?: string | null;
  /** Certificate title that proves a matched skill. */
  source?: string | null;
  /** Shows a "Prove it" link to the certificates screen for claimed or missing chips. */
  proveHref?: string;
}

export function SkillChip({ concept, kind, trustLevel, via, source, proveHref }: SkillChipProps) {
  const k = KIND[kind];
  const word = kind === "matched" && trustLevel === 2 ? "Faculty-verified" : k.word;
  const detail = kind === "near" && via ? ` via ${via}` : kind === "matched" && source ? ` · ${source}` : "";
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      <span
        className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-bold ${k.cls}`}
        title={`${concept}: ${word}${detail}`}
      >
        <k.Icon aria-hidden size={12} strokeWidth={2.5} />
        <span>{concept}</span>
        <span className="font-medium opacity-80">
          · {word}
          {detail}
        </span>
      </span>
      {proveHref && (kind === "claimed_only" || kind === "missing") ? (
        <Link href={proveHref} className="text-xs font-black text-brand underline underline-offset-2">
          Prove it<span className="sr-only"> for {concept}</span>
        </Link>
      ) : null}
    </span>
  );
}
