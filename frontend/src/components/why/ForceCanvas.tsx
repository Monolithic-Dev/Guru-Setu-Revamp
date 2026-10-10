"use client";
// Canvas half of the Why graph (A2). Loaded lazily by WhyGraph (next/dynamic, ssr:false) so the graph
// library never reaches the server bundle. It owns the ref, so it can spread links and zoom to fit.
import { useEffect, useRef } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";

export type CanvasNode = { id: string; label: string; kind: "student" | "concept" | "opening"; x?: number; y?: number };
export type CanvasLink = { source: string | CanvasNode; target: string | CanvasNode; kind: "HAS_SKILL" | "SIMILAR_TO" | "REQUIRES"; score?: number | null };

export const NODE_COLOUR: Record<CanvasNode["kind"], string> = { student: "#8C1515", concept: "#D4AF37", opening: "#1F2937" };

export interface ForceCanvasProps {
  nodes: CanvasNode[];
  links: CanvasLink[];
  width: number;
  height: number;
  reducedMotion: boolean;
}

export default function ForceCanvas({ nodes, links, width, height, reducedMotion }: ForceCanvasProps) {
  const ref = useRef<ForceGraphMethods | undefined>(undefined);

  useEffect(() => {
    const fg = ref.current;
    if (!fg) return;
    const linkForce = fg.d3Force("link") as unknown as { distance?: (d: number) => void } | undefined;
    linkForce?.distance?.(70);
    const charge = fg.d3Force("charge") as unknown as { strength?: (s: number) => void } | undefined;
    charge?.strength?.(-220);
    fg.d3ReheatSimulation();
  }, [nodes, links]);

  return (
    <ForceGraph2D
      ref={ref}
      graphData={{ nodes, links }}
      width={width}
      height={height}
      cooldownTicks={reducedMotion ? 0 : 120}
      warmupTicks={reducedMotion ? 120 : 20}
      onEngineStop={() => ref.current?.zoomToFit(reducedMotion ? 0 : 400, 40)}
      enableZoomInteraction={false}
      enablePanInteraction={false}
      linkColor={(l: object) => ((l as CanvasLink).kind === "SIMILAR_TO" ? "#B45309" : "#9CA3AF")}
      linkWidth={(l: object) => ((l as CanvasLink).kind === "SIMILAR_TO" ? 2.5 : 1.5)}
      linkLineDash={(l: object) => ((l as CanvasLink).kind === "SIMILAR_TO" ? [4, 3] : null)}
      linkDirectionalArrowLength={5}
      linkDirectionalArrowRelPos={0.85}
      linkCanvasObjectMode={() => "after"}
      linkCanvasObject={(obj: object, ctx: CanvasRenderingContext2D, scale: number) => {
        const l = obj as CanvasLink;
        if (l.kind !== "SIMILAR_TO" || typeof l.source !== "object" || typeof l.target !== "object") return;
        const x = ((l.source.x ?? 0) + (l.target.x ?? 0)) / 2;
        const y = ((l.source.y ?? 0) + (l.target.y ?? 0)) / 2;
        const size = 11 / scale;
        const text = `similar ${(l.score ?? 0).toFixed(2)}`;
        ctx.font = `bold ${size}px sans-serif`;
        const w = ctx.measureText(text).width + size * 0.8;
        ctx.fillStyle = "#FFF9E6";
        ctx.fillRect(x - w / 2, y - size * 0.75, w, size * 1.5);
        ctx.fillStyle = "#6B1010";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(text, x, y);
      }}
      nodeCanvasObject={(obj: object, ctx: CanvasRenderingContext2D, scale: number) => {
        const n = obj as CanvasNode;
        const r = (n.kind === "concept" ? 6 : 9) / Math.sqrt(scale);
        ctx.beginPath();
        ctx.arc(n.x ?? 0, n.y ?? 0, r, 0, 2 * Math.PI);
        ctx.fillStyle = NODE_COLOUR[n.kind];
        ctx.fill();
        const size = (n.kind === "concept" ? 11 : 12) / scale;
        ctx.font = `${n.kind === "concept" ? "" : "bold "}${size}px sans-serif`;
        const w = ctx.measureText(n.label).width;
        ctx.fillStyle = "rgba(242,242,242,0.85)";
        ctx.fillRect((n.x ?? 0) - w / 2 - 2 / scale, (n.y ?? 0) + r + 1 / scale, w + 4 / scale, size * 1.25);
        ctx.fillStyle = "#111827";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(n.label, n.x ?? 0, (n.y ?? 0) + r + 2 / scale);
      }}
    />
  );
}
