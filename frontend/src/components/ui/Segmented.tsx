"use client";
// Segmented toggle in the earlier GuruSetu style (grey pill track, maroon active segment).
// Built on real radio inputs, so arrow keys and screen readers work natively.
import { useId } from "react";

export interface SegmentedProps<T extends string> {
  legend: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  /** Hide the legend visually (it stays available to screen readers). */
  hideLegend?: boolean;
  name?: string;
}

export function Segmented<T extends string>({ legend, value, options, onChange, hideLegend = false, name }: SegmentedProps<T>) {
  const auto = useId();
  const group = name ?? auto;
  return (
    <fieldset>
      <legend className={hideLegend ? "sr-only" : "label"}>{legend}</legend>
      <div className="inline-flex rounded-full bg-gray-100 p-1 shadow-inner">
        {options.map((o) => {
          const id = `${group}-${o.value}`;
          const checked = o.value === value;
          return (
            <span key={o.value}>
              <input
                id={id}
                type="radio"
                name={group}
                value={o.value}
                checked={checked}
                onChange={() => onChange(o.value)}
                className="peer sr-only"
              />
              <label
                htmlFor={id}
                className={`inline-flex min-h-[40px] cursor-pointer items-center rounded-full px-4 text-xs font-black uppercase tracking-wider transition-colors peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-brand ${
                  checked ? "bg-brand text-white shadow-md" : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {o.label}
              </label>
            </span>
          );
        })}
      </div>
    </fieldset>
  );
}
