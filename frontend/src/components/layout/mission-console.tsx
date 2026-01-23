"use client";

import { useState } from "react";

import type { MissionResponse } from "@/types";

type MissionConsoleProps = {
  highlights: string[];
};

export default function MissionConsole({ highlights }: MissionConsoleProps) {
  const [mission, setMission] = useState("");
  const [result, setResult] = useState<MissionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const parseResult = (text: string) => {
    const trimmed = text.trim();
    const jsonExtract = (() => {
      if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
        try {
          const parsed = JSON.parse(trimmed) as { text?: unknown };
          if (parsed && typeof parsed === "object" && "text" in parsed) {
            return String(parsed.text ?? "");
          }
        } catch {
          return null;
        }
      }
      const match = trimmed.match(
        /\"text\"\\s*:\\s*\"([\\s\\S]*?)\"\\s*(?:,\\s*\"extras\"|,\\s*\"signature\"|\\}|$)/i,
      );
      if (match) {
        try {
          return JSON.parse(`\"${match[1]}\"`);
        } catch {
          return match[1];
        }
      }
      return null;
    })();

    const cleaned = (jsonExtract ?? trimmed)
      .replace(/\"extras\"\\s*:\\s*\\{.*$/i, "")
      .replace(/extras\\s*:\\s*\\{.*$/i, "")
      .replace(/signature\\s*:\\s*.+$/i, "")
      .replace(/\s+/g, " ")
      .trim();
    let name: string | null = null;
    let role: string | null = null;
    let org: string | null = null;

    let match = cleaned.match(
      /that (.+?) is (?:the |an |a )?(.+?) of (.+?)(?:\\.|$)/i,
    );
    if (match) {
      [, name, role, org] = match;
    } else {
      match = cleaned.match(/that (.+?) is (?:the |an |a )?(.+?)(?:\\.|$)/i);
      if (match) {
        [, name, role] = match;
      }
    }

    if (!name) {
      match = cleaned.match(/saved to (?:the )?graph[:\\s-]*(.+?)(?:\\.|$)/i);
      if (match) {
        [, name] = match;
      }
    }

    if (!name) {
      match = cleaned.match(/CEO of (.+?) (?:is|:)?\\s*(.+?)(?:\\.|$)/i);
      if (match) {
        [, org, name] = match;
        role = role ?? "CEO";
      }
    }

    if (!name) {
      match = cleaned.match(/([A-Z][\\w.'-]+(?:\\s+[A-Z][\\w.'-]+){1,3})/);
      if (match) {
        const candidate = match[1];
        const blocked = new Set(["Project Gotham", "Mission Console"]);
        if (!blocked.has(candidate)) {
          name = candidate;
        }
      }
    }

    return { cleaned, name, role, org, raw: trimmed };
  };

  const submitMission = async () => {
    if (!mission.trim()) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/run-mission", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: mission }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Mission failed");
      }

      const data = (await response.json()) as MissionResponse;
      setResult(data);
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
          <p className="text-xs uppercase tracking-[0.3em] text-[var(--surface-muted)]">
            Mission Console
          </p>
          <h2 className="font-[var(--font-display)] text-2xl text-[var(--surface-ink)]">
            New objective
          </h2>
        </div>
        <span className="rounded-full bg-[var(--surface-ink)]/10 px-3 py-1 text-xs font-semibold text-[var(--surface-ink)]">
          Thread: auto
        </span>
      </div>

      <div className="mt-6 space-y-4">
        <label className="text-xs uppercase tracking-[0.2em] text-[var(--surface-muted)]">
          Mission brief
        </label>
        <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-strong)] px-4 py-3 shadow-inner">
          <textarea
            className="h-36 w-full resize-none bg-transparent text-sm text-[var(--surface-ink)] outline-none"
            placeholder="Identify the current CEO of Delta Air Lines and the year the company was founded."
            value={mission}
            onChange={(event) => setMission(event.target.value)}
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
          <button className="h-11 rounded-full border border-[var(--surface-border)] bg-[var(--surface-bg-strong)] px-5 text-sm font-semibold text-[var(--surface-ink)]">
            Save draft
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-5 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-xs text-[var(--surface-ink)]">
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="mt-5 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-bg-soft)] px-4 py-3 text-[var(--surface-ink)] overflow-visible">
          {(() => {
            const parsed = parseResult(result.result);
            const subtitleParts = [parsed.role, parsed.org].filter(Boolean).join(" • ");
            const firstSentence =
              parsed.cleaned.split(".")[0].trim() ||
              parsed.raw.split(".")[0].trim() ||
              "";
            const fallbackName = parsed.name || firstSentence || "Mission ingested";

            return (
              <>
                <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--surface-muted)]">
                  Saved to graph
                </p>
                <p className="mt-2 text-lg font-semibold break-words">
                  {fallbackName}
                </p>
                <p className="mt-1 text-xs text-[var(--surface-muted)] break-words">
                  {subtitleParts ||
                    (parsed.cleaned ? parsed.cleaned.split(".")[0] + "." : "") ||
                    (parsed.raw ? parsed.raw.split(".")[0] + "." : "") ||
                    "Entities and relationships have been added."}
                </p>
              </>
            );
          })()}
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
