import { NextResponse } from "next/server";
import { API_BASE } from "@/lib/config";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const company = url.searchParams.get("company");
  if (!company) {
    return NextResponse.json({ detail: "company is required" }, { status: 400 });
  }

  const response = await fetch(
    `${API_BASE}/graph/competitors?company=${encodeURIComponent(company)}`,
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
