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
};

type MoodPayload = {
  mood_label?: string;
  confidence?: number;
  drivers?: string[];
  sources?: { title?: string; url?: string }[];
  timeframe?: string;
};

type MissionConsoleProps = {
  highlights: string[];
};

export default function MissionConsole({ highlights }: MissionConsoleProps) {
  const [company, setCompany] = useState("");
  const [insight, setInsight] = useState<InsightPayload | null>(null);
  const [mood, setMood] = useState<MoodPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [moodError, setMoodError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [moodLoading, setMoodLoading] = useState(false);
  const [includeMood, setIncludeMood] = useState(false);

  const submitMission = async () => {
    const target = company.trim();
    if (!target) return;
    setIsLoading(true);
    setError(null);
    setInsight(null);
    setMood(null);
    setMoodError(null);
    setMoodLoading(includeMood);

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

      if (includeMood) {
        try {
          const moodResponse = await fetch("/api/agents/company-mood", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ company: target, timeframe: "90d" }),
          });

          if (!moodResponse.ok) {
            const text = await moodResponse.text();
            throw new Error(text || "Mood fetch failed");
          }

          const moodData = (await moodResponse.json()) as MoodPayload;
          setMood(moodData);
        } catch (err) {
          setMoodError(err instanceof Error ? err.message : "Mood fetch failed");
        } finally {
          setMoodLoading(false);
        }
      }
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
          <label className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)]">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-[var(--surface-border)] bg-transparent text-[var(--surface-ink)]"
              checked={includeMood}
              onChange={(event) => setIncludeMood(event.target.checked)}
            />
            Include mood
          </label>
        </div>
      </div>

      {error ? (
        <div className="mt-5 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-xs text-[var(--surface-ink)]">
          {error}
        </div>
      ) : null}

      {insight ? (
        <div className="mt-5 space-y-4">
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

          {includeMood ? (
            <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)]">
              <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">Mood</p>
              {moodLoading ? (
                <p className="mt-2 text-sm text-[var(--surface-muted)]">Assessing mood...</p>
              ) : moodError ? (
                <p className="mt-2 text-sm text-[var(--surface-muted)]">{moodError}</p>
              ) : mood ? (
                <div className="mt-2 space-y-2 text-sm text-[var(--surface-ink)]">
                  <p className="text-lg font-semibold">
                    {mood.mood_label ?? "Mixed"}
                    {typeof mood.confidence === "number" ? ` • ${mood.confidence.toFixed(2)}` : ""}
                  </p>
                  {mood.drivers?.length ? (
                    <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--surface-muted)]">
                      {mood.drivers.map((driver, idx) => (
                        <li key={`${driver}-${idx}`}>{driver}</li>
                      ))}
                    </ul>
                  ) : null}
                  {mood.sources?.length ? (
                    <div className="flex flex-wrap gap-2 text-xs text-[var(--surface-muted)]">
                      {mood.sources.map((source, idx) => (
                        <a
                          key={`${source.url}-${idx}`}
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-full bg-[var(--surface-bg-strong)] px-3 py-1 text-[var(--surface-ink)]"
                        >
                          {source.title || "source"}
                        </a>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="mt-2 text-sm text-[var(--surface-muted)]">No mood returned.</p>
              )}
            </div>
          ) : null}

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
