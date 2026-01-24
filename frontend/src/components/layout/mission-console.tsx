"use client";

import { useState } from "react";

type InsightPayload = {
  status?: string;
  profile?: {
    name?: string;
    labels?: string[];
    properties?: Record<string, unknown>;
    sources?: { url?: string; created_at?: number }[];
    related?: { name?: string; labels?: string[]; type?: string }[];
  } | null;
  competitors?: { competitor: string; reason?: string; source?: string }[];
  profile_result?: unknown;
  competitor_result?: unknown;
  mood?: {
    label?: string | null;
    score?: number | null;
    headlines?: { title?: string; url?: string }[];
  } | null;
};

type MissionConsoleProps = {
  highlights: string[];
};

export default function MissionConsole({ highlights }: MissionConsoleProps) {
  const [company, setCompany] = useState("");
  const [insight, setInsight] = useState<InsightPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const submitMission = async () => {
    const target = company.trim();
    if (!target) return;
    setIsLoading(true);
    setError(null);
    setInsight(null);

    try {
      const response = await fetch("/api/agents/company-insight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company: target }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Mission failed");
      }

      const data = (await response.json()) as InsightPayload;
      setInsight(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mission failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="reveal delay-1 rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-bg)] p-6 text-[var(--surface-ink)] shadow-lg backdrop-blur">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[var(--surface-muted)]">Mission Console</p>
          <h2 className="font-[var(--font-display)] text-2xl text-[var(--surface-ink)]">New objective</h2>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        <label className="text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)]">Mission brief</label>
        <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-strong)] px-4 py-3 shadow-inner">
          <input
            className="h-12 w-full bg-transparent text-sm text-[var(--surface-ink)] outline-none"
            placeholder="Enter a company (e.g., Meta Platforms, Inc.)"
            value={company}
            onChange={(event) => setCompany(event.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitMission();
            }}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            className="h-11 rounded-full bg-[var(--surface-ink)] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
            onClick={submitMission}
            disabled={isLoading}
          >
            {isLoading ? "Dispatching..." : "Dispatch mission"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-5 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-xs text-[var(--surface-ink)]">
          {error}
        </div>
      ) : null}

      {insight ? (
        <div className="mt-5 space-y-4">
          {insight.mood ? (
            <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)] flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">Mood</p>
                {insight.mood.label ? (
                  <span className="rounded-full bg-[var(--surface-bg-strong)] px-3 py-1 text-xs font-semibold text-[var(--surface-ink)]">
                    {insight.mood.label} {insight.mood.score !== undefined && insight.mood.score !== null ? `(${Number(insight.mood.score).toFixed(2)})` : ""}
                  </span>
                ) : null}
              </div>
              {insight.mood.headlines?.length ? (
                <ul className="space-y-1 text-sm text-[var(--surface-ink)]">
                  {insight.mood.headlines.slice(0, 3).map((h, idx) => (
                    <li key={idx} className="break-words">
                      {h.url ? (
                        <a className="underline" href={h.url} target="_blank" rel="noreferrer">
                          {h.title ?? h.url}
                        </a>
                      ) : (
                        <span>{h.title}</span>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[var(--surface-muted)]">No headlines returned.</p>
              )}
            </div>
          ) : null}

          <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)]">
            <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">Profile</p>
            {insight.profile ? (
              <div className="mt-2 space-y-2">
                <p className="text-lg font-semibold break-words">{insight.profile.name ?? "Saved to graph"}</p>
                {insight.profile.related?.length ? (
                  <div className="flex flex-wrap gap-2 text-xs text-[var(--surface-muted)]">
                    {insight.profile.related.slice(0, 8).map((r, idx) => (
                      <span
                        key={`${r.name}-${idx}`}
                        className="rounded-full bg-[var(--surface-bg-strong)] px-3 py-1 text-[var(--surface-ink)]"
                      >
                        {r.name} {r.type ? `• ${r.type}` : ""}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[var(--surface-muted)]">No related entities yet.</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-[var(--surface-muted)]">No profile returned.</p>
            )}
          </div>

          <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)]">
            <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">Competitors</p>
            {insight.competitors?.length ? (
              <ul className="mt-2 space-y-2 text-sm text-[var(--surface-ink)]">
                {insight.competitors.map((c, idx) => (
                  <li key={`${c.competitor}-${idx}`} className="break-words">
                    <span className="font-semibold">{c.competitor}</span>
                    {c.reason ? ` — ${c.reason}` : ""}
                    {c.source ? (
                      <>
                        {" "}
                        <a className="text-[var(--surface-ink)] underline" href={c.source} target="_blank" rel="noreferrer">
                          source
                        </a>
                      </>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-[var(--surface-muted)]">No competitors returned.</p>
            )}
          </div>

          {(insight.profile_result || insight.competitor_result) && (
            <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-xs text-[var(--surface-muted)]">
              <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">Raw agent output</p>
              {insight.profile_result ? <pre className="mt-2 whitespace-pre-wrap break-words">{JSON.stringify(insight.profile_result, null, 2)}</pre> : null}
              {insight.competitor_result ? <pre className="mt-2 whitespace-pre-wrap break-words">{JSON.stringify(insight.competitor_result, null, 2)}</pre> : null}
            </div>
          )}
        </div>
      ) : null}

      <div className="mt-6 grid gap-3 text-xs text-[var(--surface-muted)]">
        {highlights.map((item) => (
          <div key={item} className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[var(--surface-ink)]" />
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}
