// Read-only fit for one applicant on SCR-09 (REQ-005). Interim view built from the UI kit until P1's
// components/fit/FitPanel lands (seam due 7:30); swap the import on SCR-09 then. No scoring happens here.
import { SkillChip } from "@/components/ui";
import { formatScore } from "@/lib/format";
import type { components } from "@/lib/types";

type Fit = components["schemas"]["Fit"];

const PARTS: { key: keyof Fit["components"]; label: string; cls: string }[] = [
  { key: "semantic", label: "Semantic", cls: "bg-brand" },
  { key: "skill", label: "Skill", cls: "bg-gold" },
  { key: "concept", label: "Concept", cls: "bg-gray-500" },
];

const GROUPS: { kind: Fit["chips"][number]["kind"]; title: string }[] = [
  { kind: "matched", title: "Matched" },
  { kind: "claimed_only", title: "Claimed only" },
  { kind: "near", title: "Near" },
  { kind: "missing", title: "Missing" },
];

export function CandidateFit({ fit }: { fit: Fit }) {
  return (
    <div className="space-y-4">
      <div>
        <p className="mb-1 text-xs font-black uppercase tracking-widest text-gray-600">Score breakdown</p>
        <div className="flex h-3 w-full overflow-hidden rounded-full bg-gray-100" aria-hidden>
          {PARTS.map((p) => (
            <span key={p.key} className={p.cls} style={{ width: `${Math.max(0, fit.components[p.key])}%` }} />
          ))}
        </div>
        <p className="mt-1 text-sm text-gray-800">
          {PARTS.map((p) => `${p.label} ${formatScore(fit.components[p.key])}`).join(" + ")} = <span className="font-black">{formatScore(fit.score)}</span>
        </p>
      </div>
      {GROUPS.map((g) => {
        const chips = fit.chips.filter((c) => c.kind === g.kind);
        if (chips.length === 0) return null;
        return (
          <div key={g.kind}>
            <p className="mb-1 text-xs font-black uppercase tracking-widest text-gray-600">{g.title}</p>
            <div className="flex flex-wrap gap-2">
              {chips.map((c) => (
                <SkillChip key={c.concept} concept={c.concept} kind={c.kind} trustLevel={c.trust_level} via={c.via} source={c.source?.title} />
              ))}
            </div>
          </div>
        );
      })}
      {fit.note ? <p className="text-sm text-gray-700">{fit.note}</p> : null}
    </div>
  );
}
