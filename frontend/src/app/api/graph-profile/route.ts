import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const name = url.searchParams.get("name");
  if (!name) {
    return NextResponse.json({ detail: "name is required" }, { status: 400 });
  }

  const response = await fetch(
    `${API_BASE}/graph/profile?name=${encodeURIComponent(name)}`,
    { method: "GET" },
  );

  const text = await response.text();
  try {
    const data = JSON.parse(text);
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ raw: text }, { status: response.status });
  }
}
