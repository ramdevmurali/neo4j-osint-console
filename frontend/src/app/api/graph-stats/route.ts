import { NextResponse } from "next/server";
import { API_BASE } from "@/lib/config";

export async function GET() {
  const response = await fetch(`${API_BASE}/graph/stats`);
  const text = await response.text();
  try {
    const data = JSON.parse(text);
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { entities: 0, sources: 0, dedupe_confidence: 100, raw: text },
      { status: response.status },
    );
  }
}
