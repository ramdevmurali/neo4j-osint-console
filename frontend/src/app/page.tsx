'use client';

import MissionConsole from "@/components/layout/mission-console";
import Pill from "@/components/ui/pill";
import StatCard from "@/components/ui/stat-card";
import ThemeToggle from "@/components/ui/theme-toggle";
import GraphPreview, { type GraphEdge, type GraphNode } from "@/components/ui/graph-preview";
import { missionHighlights, stats as staticStats } from "@/lib/content";
import { useEffect, useState } from "react";
import { fetchJson } from "@/lib/fetcher";
import { SAMPLE_DOC_LIMIT } from "@/lib/constants";

type GraphSample = {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  node_count?: number;
  edge_count?: number;
  documents?: { url?: string }[];
};

export default function Home() {
  const [sampleSummary, setSampleSummary] = useState<{
    node_count: number;
    edge_count: number;
    sample_nodes: string[];
    documents: { url?: string }[];
  } | null>(null);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [showGraph, setShowGraph] = useState(false);
  const [stats, setStats] = useState(staticStats);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const resp = await fetch("/api/graph-stats");
        if (!resp.ok) throw new Error(`Stats fetch failed: ${resp.status}`);
        const data = await resp.json();
        setStats([
          { value: String(data.entities ?? 0), label: "entities tracked" },
          { value: String(data.sources ?? 0), label: "sources indexed" },
        ]);
      } catch (err) {
        setStatsError(err instanceof Error ? err.message : "Could not load stats");
      }
    };
    loadStats();
  }, []);

  const handleViewSample = async () => {
    // toggle off
    if (showGraph) {
      setShowGraph(false);
      return;
    }
    // always fetch fresh on open
    setSampleLoading(true);
    setSampleError(null);
    try {
      const { response, data } = await fetchJson<GraphSample>(`/api/run-mission?doc_limit=${SAMPLE_DOC_LIMIT}`);
      if (!response.ok) {
        throw new Error(`Backend responded ${response.status}`);
      }
      const graphData: GraphSample = data && typeof data === "object" ? (data as GraphSample) : {};
      const names: string[] = [];
      if (Array.isArray(graphData.nodes)) {
        for (const node of graphData.nodes.slice(0, SAMPLE_DOC_LIMIT)) {
          if (node && typeof node === "object" && "name" in node) {
            const name = String((node as { name?: unknown }).name ?? "");
            if (name) names.push(name);
          }
        }
      }
      setSampleSummary({
        node_count: graphData.node_count ?? 0,
        edge_count: graphData.edge_count ?? 0,
        sample_nodes: names,
        documents: Array.isArray(graphData.documents) ? graphData.documents : [],
      });
      setGraphNodes(Array.isArray(graphData.nodes) ? graphData.nodes : []);
      setGraphEdges(Array.isArray(graphData.edges) ? graphData.edges : []);
      setShowGraph(true);
    } catch {
      // Keep any prior graph visible; only show a friendly message.
      setSampleError("Could not load graph sample. Please retry.");
    } finally {
      setSampleLoading(false);
    }
  };

  return (
    <div className="page-shell">
      <div className="float-glow one" />
      <div className="float-glow two" />
      <div className="grain" />

      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-14 px-6 pb-24 pt-10 sm:px-10 lg:px-16">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="h-10 w-10 rounded-2xl bg-[var(--ink)] text-[var(--parchment)] flex items-center justify-center font-semibold">
              G
            </span>
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-[var(--ink-muted)]">
                Project Gotham
              </p>
              <p className="font-[var(--font-display)] text-lg text-[var(--ink)]">
                Intelligence Console
              </p>
            </div>
          </div>
          <ThemeToggle />
        </nav>

        <section className="space-y-10">
          <div className="flex flex-col gap-6">
            <Pill>OSINT missions → Graph entities</Pill>
            <div className="space-y-6">
              <h1 className="reveal delay-1 font-[var(--font-display)] text-4xl leading-tight text-[var(--ink)] sm:text-5xl lg:text-6xl">
                Turn open-source signals into a living intelligence graph.
              </h1>
              <p className="reveal delay-2 text-base leading-7 text-[var(--ink-muted)] sm:text-lg">
                Project Gotham stitches sources, entities, and relationships in real time.
                Drop a mission, watch the graph populate, and keep every source traceable.
              </p>
            </div>
          </div>

          <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-start">
            <div className="space-y-6">
              <div className="reveal delay-3 flex flex-wrap items-center gap-4">
                <button
                  className="h-12 rounded-full border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-6 text-sm font-semibold text-[var(--surface-ink)] transition hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-60"
                  onClick={handleViewSample}
                  disabled={sampleLoading}
                >
                  {sampleLoading ? "Loading..." : showGraph ? "Hide sample graph" : "View sample graph"}
                </button>
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--ink-muted)]">
                  Aura-ready • Neo4j
                </div>
              </div>

              <div className="reveal delay-3 rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-bg)] p-5 text-[var(--surface-ink)] shadow-lg backdrop-blur">
                <p className="text-xs uppercase tracking-[0.28em] text-[var(--surface-muted)]">
                  Sample graph
                </p>
                {sampleLoading ? (
                  <div className="mt-2 space-y-2">
                    <div className="h-5 w-40 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
                    <div className="h-4 w-64 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
                    <div className="h-3 w-48 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
                    <div className="mt-3 h-64 animate-pulse rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-strong)]" />
                  </div>
                ) : sampleSummary ? (
                  <>
                    <p className="mt-1 font-semibold">
                      {sampleSummary.node_count} nodes · {sampleSummary.edge_count} edges
                    </p>
                    {sampleSummary.sample_nodes.length ? (
                      <p className="mt-1 text-sm text-[var(--surface-muted)]">
                        {sampleSummary.sample_nodes.join(" • ")}
                      </p>
                    ) : null}
                    {sampleSummary.documents.length ? (
                      <p className="mt-1 text-[var(--surface-muted)] text-xs">
                        from {Math.min(sampleSummary.documents.length, 5)} recent sources
                      </p>
                    ) : null}
                    {sampleError ? (
                      <p className="mt-2 text-sm text-[var(--surface-ink)]">{sampleError}</p>
                    ) : null}
                    <div className="mt-3">
                      {showGraph ? (
                        <GraphPreview nodes={graphNodes} edges={graphEdges} />
                      ) : (
                        <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-8 text-center text-xs text-[var(--surface-muted)]">
                          Sample graph hidden.
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="mt-2 text-sm text-[var(--surface-muted)]">
                    Load a sample to preview the graph.
                  </p>
                )}
                {sampleError && !sampleLoading ? (
                  <p className="mt-2 text-sm text-[var(--surface-ink)]">{sampleError}</p>
                ) : null}
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {stats.map((stat) => (
                  <StatCard key={stat.label} value={stat.value} label={stat.label} />
                ))}
              </div>
              {statsError ? (
                <p className="text-xs text-[var(--ink-muted)]">{statsError}</p>
              ) : null}
            </div>

            <MissionConsole highlights={missionHighlights.slice(0, 1)} />
          </div>
        </section>

      </main>
    </div>
  );
}
