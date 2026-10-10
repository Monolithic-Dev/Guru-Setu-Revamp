"use client";
// Topic categories as toggle buttons (ux-flows §7: role="group", aria-pressed).
import { Check } from "lucide-react";
import type { components } from "@/lib/types";

export type Topic = components["schemas"]["TopicCategory"];

export const TOPICS: { value: Topic; label: string }[] = [
  { value: "academic", label: "Academic" },
  { value: "attendance", label: "Attendance" },
  { value: "career", label: "Career" },
  { value: "research", label: "Research" },
  { value: "personal", label: "Personal" },
  { value: "other", label: "Other" },
];

export interface TopicChipsProps {
  id?: string;
  value: Topic[];
  onChange: (value: Topic[]) => void;
  labelledBy: string;
  describedBy?: string;
}

export function TopicChips({ id, value, onChange, labelledBy, describedBy }: TopicChipsProps) {
  return (
    <div id={id} role="group" aria-labelledby={labelledBy} aria-describedby={describedBy} tabIndex={-1} className="flex flex-wrap gap-2 outline-none">
      {TOPICS.map((t) => {
        const on = value.includes(t.value);
        return (
          <button
            key={t.value}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(on ? value.filter((v) => v !== t.value) : [...value, t.value])}
            className={`inline-flex min-h-[40px] items-center gap-1.5 rounded-full border px-4 text-sm font-bold transition-colors ${
              on ? "border-brand bg-brand text-white" : "border-gray-300 bg-white text-gray-700 hover:border-brand hover:text-brand"
            }`}
          >
            {on ? <Check aria-hidden size={14} strokeWidth={3} /> : null}
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
