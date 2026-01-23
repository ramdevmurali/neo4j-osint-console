'use client';

import dynamic from "next/dynamic";
import { useMemo } from "react";

// Use the 2D-only build to avoid AFRAME (VR) globals in the browser.
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export type GraphNode = {
  id: string;
  name?: string;
  labels?: string[];
  props?: Record<string, unknown>;
};

export type GraphEdge = {
  id?: string;
  source: string;
  target: string;
  type?: string;
  props?: Record<string, unknown>;
};

type GraphPreviewProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  height?: number;
};

const labelColor = (labels: string[] | undefined) => {
  const label = labels?.[0] ?? "Other";
  switch (label) {
    case "Person":
      return "#f97316"; // orange
    case "Organization":
      return "#06b6d4"; // teal
    case "Location":
      return "#22c55e"; // green
    case "Topic":
      return "#a855f7"; // purple
    default:
      return "#e5e7eb"; // gray
  }
};

export default function GraphPreview({ nodes, edges, height = 360 }: GraphPreviewProps) {
  const data = useMemo(() => {
    // cap to avoid perf blowups
    const maxNodes = 60;
    const trimmedNodes = nodes.slice(0, maxNodes);
    const allowedIds = new Set(trimmedNodes.map((n) => n.id));
    const trimmedEdges = edges.filter(
      (e) => allowedIds.has(String(e.source)) && allowedIds.has(String(e.target)),
    );
    return { nodes: trimmedNodes, links: trimmedEdges };
  }, [nodes, edges]);

  if (!data.nodes.length) {
    return (
      <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-sm text-[var(--surface-ink)]">
        No sample nodes yet. Run a mission to populate the graph.
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] p-3">
      <ForceGraph2D
        width={undefined}
        height={height}
        graphData={data}
        cooldownTicks={40}
        nodeRelSize={6}
        linkColor={() => "rgba(255,255,255,0.2)"}
        linkWidth={1}
        backgroundColor="transparent"
        nodeCanvasObject={(node, ctx, globalScale) => {
          const typed = node as GraphNode;
          const label = typed.name || "node";
          const color = labelColor(typed.labels);
          const r = 6;
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, 2 * Math.PI, false);
          ctx.fillStyle = color;
          ctx.fill();
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px Inter, system-ui`;
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "rgba(255,255,255,0.9)";
          ctx.fillText(label, (node.x ?? 0) + r + 2, node.y ?? 0);
        }}
        nodeLabel={(node) => {
          const typed = node as GraphNode;
          return `${typed.name ?? "node"}${typed.labels?.length ? " · " + typed.labels[0] : ""}`;
        }}
      />
    </div>
  );
}
