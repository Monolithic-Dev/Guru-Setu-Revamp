"use client";
// "Why this match?" graph (add-on A2, REQ-020, API-020). P1's SCR-03 renders it behind `features.whyGraph`.
// The canvas is decoration for sighted users; the same paths are written below as a text list (a11y).
import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { ErrorState, LoadingRegion, Skeleton } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import type { components } from "@/lib/types";

type Why = components["schemas"]["WhyGraph"];
type WhyNode = Why["nodes"][number];

const ForceCanvas = dynamic(() => import("./ForceCanvas"), {
  ssr: false,
  loading: () => <div aria-hidden className="h-[360px] animate-pulse rounded-2xl bg-gray-100" />,
});

export interface WhyGraphProps {
  openingId: string;
}

// Same colours as ForceCanvas.NODE_COLOUR (kept here so the legend renders without the lazy chunk).
const COLOUR: Record<WhyNode["kind"], string> = { student: "#8C1515", concept: "#D4AF37", opening: "#1F2937" };
const KIND_LABEL: Record<WhyNode["kind"], string> = { student: "Student", concept: "Skill", opening: "Opening" };

/** Readable paths from the graph: student → skill → (similar) → required skill ← opening. */
export function whyPaths(g: Why): string[] {
  const label = new Map(g.nodes.map((n) => [n.id, n.label]));
  const student = g.nodes.find((n) => n.kind === "student");
  const opening = g.nodes.find((n) => n.kind === "opening");
  if (!student || !opening) return [];
  const held = new Set(g.edges.filter((e) => e.kind === "HAS_SKILL").map((e) => e.target));
  const similar = g.edges.filter((e) => e.kind === "SIMILAR_TO");
  const required = g.edges.filter((e) => e.kind === "REQUIRES").map((e) => e.target);
  const by = `required by ${opening.label}`;
  return required.map((r) => {
    const name = label.get(r) ?? r;
    if (held.has(r)) return `${student.label} → has skill → ${name} → ${by}`;
    const near = similar.find((e) => (e.source === r && held.has(e.target)) || (e.target === r && held.has(e.source)));
    if (near) {
      const via = near.source === r ? near.target : near.source;
      return `${label.get(via) ?? via} → similar to (${(near.score ?? 0).toFixed(2)}) → ${name} → ${by}`;
    }
    return `${name} → ${by} (not held yet)`;
  });
}


export default function WhyGraph({ openingId }: WhyGraphProps) {
  const { data, error, loading, reload } = useApi<Why>(`/openings/${openingId}/why`);
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(600);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(260, Math.floor(entry.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, [data]);

  const graph = useMemo(
    () => (data ? { nodes: data.nodes.map((n) => ({ ...n })), links: data.edges.map((e) => ({ ...e })) } : null),
    [data],
  );
  const paths = useMemo(() => (data ? whyPaths(data) : []), [data]);

  return (
    <section aria-labelledby={`why-${openingId}`} className="card space-y-3">
      <h2 id={`why-${openingId}`} className="section-title">
        Why this match?
      </h2>
      {loading ? (
        <LoadingRegion label="Loading the match graph">
          <Skeleton block />
        </LoadingRegion>
      ) : error ? (
        <ErrorState inline error={error} onRetry={reload} />
      ) : graph ? (
        <>
          <div ref={box} aria-hidden className="h-[360px] overflow-hidden rounded-2xl border border-gray-100 bg-canvas">
            <ForceCanvas nodes={graph.nodes} links={graph.links} width={width} height={360} reducedMotion={reduced} />
          </div>
          <ul className="flex flex-wrap gap-3 text-xs font-bold text-gray-700" aria-label="Legend">
            {(Object.keys(COLOUR) as WhyNode["kind"][]).map((k) => (
              <li key={k} className="inline-flex items-center gap-1.5">
                <span aria-hidden className="h-3 w-3 rounded-full" style={{ background: COLOUR[k] }} />
                {KIND_LABEL[k]}
              </li>
            ))}
            <li className="inline-flex items-center gap-1.5">
              <span aria-hidden className="h-0 w-5 border-t-2 border-dashed border-amber-700" /> Similar skill
            </li>
          </ul>
          <div>
            <h3 className="mb-1 text-xs font-black uppercase tracking-widest text-gray-600">Paths</h3>
            <ul className="space-y-1">
              {paths.map((p) => (
                <li key={p} className="text-sm text-gray-800">
                  {p}
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : null}
    </section>
  );
}
