"use client";
// Eligibility rules for one opening, each in plain words (plan section 4.2). Shown above the fit panel: eligibility
// ("can I apply?") is a separate question from fit ("how well do I match?"), and CGPA only ever appears here.
import { CircleAlert, CircleCheck, CircleHelp } from "lucide-react";
import { useApi } from "@/hooks/useApi";
import type { components } from "@/lib/types";

type Eligibility = components["schemas"]["Eligibility"];

const ICON = {
  ok: { Icon: CircleCheck, cls: "text-green-700", word: "Met" },
  failed: { Icon: CircleAlert, cls: "text-red-700", word: "Not met" },
  unknown: { Icon: CircleHelp, cls: "text-gray-600", word: "Unknown" },
} as const;

export function EligibilityChecklist({ openingId }: { openingId: string }) {
  const { data } = useApi<Eligibility>(`/openings/${openingId}/eligibility`);
  if (!data) return null;
  const heading = data.eligible
    ? "You meet the requirements"
    : data.mode === "strict"
      ? "You can't apply yet"
      : "You can still apply, but note:";
  return (
    <section aria-labelledby="elig-title" className="card space-y-2">
      <h2 id="elig-title" className="section-title">Can I apply?</h2>
      <p className="text-sm font-black text-gray-900">{heading}</p>
      <ul className="space-y-1.5">
        {data.checks.map((c) => {
          const { Icon, cls, word } = ICON[c.status];
          return (
            <li key={c.rule} className="flex items-start gap-2 text-sm text-gray-800">
              <Icon aria-hidden size={18} className={`mt-0.5 shrink-0 ${cls}`} />
              <span>
                <span className="sr-only">{word}: </span>
                {c.detail}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
