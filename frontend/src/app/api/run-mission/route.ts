import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";

export async function POST(request: Request) {
  const payload = await request.json();

  const response = await fetch(`${API_BASE}/run-mission`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const text = await response.text();

  const extractText = (input: unknown): string => {
    if (Array.isArray(input)) {
      for (const item of input) {
        if (item && typeof item === "object" && "text" in item) {
          return String((item as { text?: unknown }).text ?? "");
        }
        if (typeof item === "string") {
          return item;
        }
      }
      return "";
    }
    if (typeof input === "string") {
      const trimmed = input.trim();
      if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
        try {
          const parsed = JSON.parse(trimmed) as { text?: unknown };
          if (parsed && typeof parsed === "object" && "text" in parsed) {
            return String(parsed.text ?? "");
          }
        } catch {
          // fall through to regex extraction
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

      if (trimmed.includes("\"extras\"")) {
        return trimmed.split("\"extras\"")[0].replace(/^[{,\\s]+/g, "").trim();
      }

      return trimmed;
    }

    if (input && typeof input === "object" && "text" in (input as object)) {
      return String((input as { text?: unknown }).text ?? "");
    }

    return "";
  };

  const sanitize = (raw: string) =>
    raw
      .replace(/\"extras\"\\s*:\\s*\\{[\\s\\S]*$/i, "")
      .replace(/extras\\s*:\\s*\\{[\\s\\S]*$/i, "")
      .replace(/\"signature\"\\s*:\\s*\"[\\s\\S]*$/i, "")
      .replace(/signature\\s*:\\s*[\\s\\S]*$/i, "")
      .trim();

  try {
    const data = JSON.parse(text) as { result?: unknown; thread_id?: string; status?: string };
    const rawResult = extractText(data.result);
    const normalizedResult = sanitize(rawResult) || rawResult;

    return NextResponse.json(
      {
        ...data,
        result: normalizedResult,
      },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      {
        result: text,
        thread_id: "",
        status: response.ok ? "success" : "error",
      },
      { status: response.status },
    );
  }
}
