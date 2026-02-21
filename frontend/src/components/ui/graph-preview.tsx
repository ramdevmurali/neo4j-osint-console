'use client';

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";

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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [width, setWidth] = useState(680);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const { width: w } = entries[0].contentRect;
      setWidth(w);
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const data = useMemo(() => {
    // Deduplicate by (labels, lowercased trimmed name) to avoid duplicate concept nodes.
    const nameKey = (n: GraphNode) => {
        const labelSig = (n.labels ?? []).sort().join("|") || "None";
        const norm = (n.name ?? "").trim().toLowerCase();
        return `${labelSig}::${norm}`;
    };
    const nodeMap = new Map<string, GraphNode>();
    for (const n of nodes) {
      if (!n.name) continue;
      const key = nameKey(n);
      if (!nodeMap.has(key)) {
        nodeMap.set(key, n);
      }
    }
    const dedupedNodes = Array.from(nodeMap.values());

    // Remap edges to canonical node ids based on deduped nodes.
    const idByKey = new Map<string, string>();
    for (const n of dedupedNodes) {
      idByKey.set(nameKey(n), n.id);
    }

    const remappedEdges: GraphEdge[] = [];
    for (const e of edges) {
      // Find the node objects for the source/target ids in the original list.
      const srcNode = nodes.find((n) => String(n.id) === String(e.source));
      const tgtNode = nodes.find((n) => String(n.id) === String(e.target));
      if (!srcNode || !tgtNode || !srcNode.name || !tgtNode.name) continue;
      const srcKey = nameKey(srcNode);
      const tgtKey = nameKey(tgtNode);
      const srcCanonical = idByKey.get(srcKey);
      const tgtCanonical = idByKey.get(tgtKey);
      if (!srcCanonical || !tgtCanonical) continue;
      if (srcCanonical === tgtCanonical) continue; // skip self after remap
      remappedEdges.push({
        ...e,
        source: srcCanonical,
        target: tgtCanonical,
      });
    }

    // cap to avoid perf blowups
    const maxNodes = 60;
    const trimmedNodes = dedupedNodes.slice(0, maxNodes);
    const allowedIds = new Set(trimmedNodes.map((n) => n.id));
    const trimmedEdges = remappedEdges.filter(
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
    <div
      ref={containerRef}
      className="rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] p-3"
    >
      <ForceGraph2D
        width={width}
        height={height}
        graphData={data}
        cooldownTicks={40}
        nodeRelSize={6}
        linkColor={() => "rgba(125, 0, 6, 0.35)"}
        linkWidth={1}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.6}
        maxZoom={2.5}
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

          const textWidth = ctx.measureText(label).width;
          const paddingX = 4 / globalScale;
          const paddingY = 2 / globalScale;
          const x = (node.x ?? 0) + r + 3;
          const y = node.y ?? 0;

          // halo/pill behind text for readability on light backgrounds
          ctx.fillStyle = getComputedStyle(document.documentElement)
            .getPropertyValue("--surface-bg")
            .trim() || "rgba(255,255,255,0.92)";
          const rectX = x - paddingX;
          const rectY = y - fontSize / 2 - paddingY;
          const rectW = textWidth + paddingX * 2;
          const rectH = fontSize + paddingY * 2;
          const radius = 4 / globalScale;
          ctx.beginPath();
          ctx.moveTo(rectX + radius, rectY);
          ctx.lineTo(rectX + rectW - radius, rectY);
          ctx.quadraticCurveTo(rectX + rectW, rectY, rectX + rectW, rectY + radius);
          ctx.lineTo(rectX + rectW, rectY + rectH - radius);
          ctx.quadraticCurveTo(rectX + rectW, rectY + rectH, rectX + rectW - radius, rectY + rectH);
          ctx.lineTo(rectX + radius, rectY + rectH);
          ctx.quadraticCurveTo(rectX, rectY + rectH, rectX, rectY + rectH - radius);
          ctx.lineTo(rectX, rectY + radius);
          ctx.quadraticCurveTo(rectX, rectY, rectX + radius, rectY);
          ctx.fill();

          ctx.fillStyle = getComputedStyle(document.documentElement)
            .getPropertyValue("--surface-ink")
            .trim() || "rgba(12,20,32,0.98)";
          ctx.fillText(label, x, y);
        }}
        nodeLabel={(node) => {
          const typed = node as GraphNode;
          return `${typed.name ?? "node"}${typed.labels?.length ? " · " + typed.labels[0] : ""}`;
        }}
      />
    </div>
  );
}
