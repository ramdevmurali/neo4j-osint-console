"use client";

import { useState } from "react";
import { fetchJson } from "@/lib/fetcher";

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
  const [showAllCompetitors, setShowAllCompetitors] = useState(false);
  const [showAllDrivers, setShowAllDrivers] = useState(false);
  const [activeTab, setActiveTab] = useState<"competitors" | "mood">("competitors");

  const submitMission = async () => {
    const target = company.trim();
    if (!target) return;
    setIsLoading(true);
    setError(null);
    setMoodError(null);
    setMoodLoading(includeMood);
    setShowAllCompetitors(false);
    setShowAllDrivers(false);
    setActiveTab("competitors");

    try {
      const insightPromise = (async () => {
        const { response, data } = await fetchJson<InsightPayload>("/api/agents/company-insight", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ company: target }),
        });
        if (!response.ok) {
          const msg = typeof data === "string" && data ? data : "Mission failed";
          throw new Error(msg);
        }
        setInsight(data as InsightPayload);
      })();

      const moodPromise = includeMood
        ? (async () => {
            try {
              const { response, data } = await fetchJson<MoodPayload>("/api/agents/company-mood", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ company: target, timeframe: "90d" }),
              });

              if (!response.ok) {
                const msg = typeof data === "string" && data ? data : "Mood fetch failed";
                throw new Error(msg);
              }

              setMood(data as MoodPayload);
            } catch (err) {
              setMoodError(err instanceof Error ? err.message : "Mood fetch failed");
            } finally {
              setMoodLoading(false);
            }
          })()
        : Promise.resolve();

      await Promise.all([insightPromise, moodPromise]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mission failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="reveal delay-1 rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-bg)] p-5 text-[var(--surface-ink)] shadow-lg backdrop-blur">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[var(--surface-muted)]">Mission Console</p>
          <h2 className="font-[var(--font-display)] text-2xl text-[var(--surface-ink)]">New objective</h2>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <label className="text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)]">Mission brief</label>
        <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-strong)] px-4 py-3 shadow-inner">
          <input
            className="h-11 w-full bg-transparent text-sm text-[var(--surface-ink)] outline-none"
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
            className="h-10 rounded-full bg-[var(--surface-ink)] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
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
          <span className="text-[0.65rem] text-[var(--surface-muted)]">Mood adds ~8–12s</span>
        </div>
      </div>

      {error ? (
        <div className="mt-4 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-xs text-[var(--surface-ink)]">
          {error}
        </div>
      ) : null}

      {isLoading && !insight ? (
        <div className="mt-4 space-y-3">
          <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)]">
            <div className="h-4 w-28 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
            <div className="mt-3 h-5 w-48 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
            <div className="mt-4 flex flex-col gap-2">
              <div className="h-3 w-32 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
              <div className="h-3 w-40 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
              <div className="h-3 w-28 animate-pulse rounded bg-[var(--surface-bg-strong)]" />
            </div>
          </div>
        </div>
      ) : insight ? (
        <div className="mt-4 space-y-3">
          <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)]">
            <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">Company</p>
            <div className="mt-2 space-y-3">
              <p className="text-lg font-semibold break-words">
                {insight.profile?.name ?? company}
              </p>
              {isLoading ? (
                <span className="inline-flex items-center gap-2 rounded-full bg-[var(--surface-bg-strong)] px-3 py-1 text-xs text-[var(--surface-muted)]">
                  Updating…
                </span>
              ) : null}
              <div className="flex flex-wrap gap-2 text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)]">
                <button
                  className={`rounded-full px-3 py-1 ${activeTab === "competitors" ? "bg-[var(--surface-ink)] text-white" : "bg-[var(--surface-bg-strong)] text-[var(--surface-ink)]"}`}
                  onClick={() => setActiveTab("competitors")}
                >
                  Competitors
                </button>
                <button
                  className={`rounded-full px-3 py-1 ${activeTab === "mood" ? "bg-[var(--surface-ink)] text-white" : "bg-[var(--surface-bg-strong)] text-[var(--surface-ink)]"}`}
                  onClick={() => setActiveTab("mood")}
                >
                  Mood
                </button>
              </div>

              {activeTab === "competitors" ? (
                insight.competitors?.length ? (
                  <ul className="space-y-2 text-sm text-[var(--surface-ink)]">
                    {(showAllCompetitors ? insight.competitors : insight.competitors.slice(0, 3)).map((c, idx) => {
                      const reason =
                        !showAllCompetitors && c.reason && c.reason.length > 140
                          ? `${c.reason.slice(0, 140)}…`
                          : c.reason;
                      return (
                        <li key={`${c.competitor}-${idx}`} className="break-words">
                          <span className="font-semibold">{c.competitor}</span>
                          {reason ? ` — ${reason}` : ""}
                          {c.source ? (
                            <>
                              {" "}
                              <a className="text-[var(--surface-ink)] underline" href={c.source} target="_blank" rel="noreferrer">
                                source
                              </a>
                            </>
                          ) : null}
                        </li>
                      );
                    })}
                    {insight.competitors.length > 3 ? (
                      <li>
                        <button
                          className="text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)] underline"
                          onClick={() => setShowAllCompetitors((prev) => !prev)}
                        >
                          {showAllCompetitors ? "Show less" : "Show more"}
                        </button>
                      </li>
                    ) : null}
                  </ul>
                ) : (
                  <p className="text-sm text-[var(--surface-muted)]">No competitors returned.</p>
                )
              ) : includeMood ? (
                moodLoading ? (
                  <p className="text-sm text-[var(--surface-muted)]">Assessing mood...</p>
                ) : moodError ? (
                  <p className="text-sm text-[var(--surface-muted)]">{moodError}</p>
                ) : mood ? (
                  <div className="space-y-2 text-sm text-[var(--surface-ink)]">
                    <p className="text-lg font-semibold">
                      {mood.mood_label ?? "Mixed"}
                      {typeof mood.confidence === "number" ? ` • ${mood.confidence.toFixed(2)}` : ""}
                    </p>
                    {mood.drivers?.length ? (
                      <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--surface-muted)]">
                        {(showAllDrivers ? mood.drivers : mood.drivers.slice(0, 2)).map((driver, idx) => (
                          <li key={`${driver}-${idx}`}>{driver}</li>
                        ))}
                      </ul>
                    ) : null}
                    {mood.drivers && mood.drivers.length > 2 ? (
                      <button
                        className="text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)] underline"
                        onClick={() => setShowAllDrivers((prev) => !prev)}
                      >
                        {showAllDrivers ? "Show less" : "Show more"}
                      </button>
                    ) : null}
                    {mood.sources?.length ? (
                      <div className="flex flex-wrap gap-2 text-xs text-[var(--surface-muted)]">
                        {mood.sources.slice(0, 2).map((source, idx) => (
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
                  <p className="text-sm text-[var(--surface-muted)]">No mood returned.</p>
                )
              ) : (
                <p className="text-sm text-[var(--surface-muted)]">Enable mood to see sentiment signals.</p>
              )}
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-2 text-xs text-[var(--surface-muted)]">
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
