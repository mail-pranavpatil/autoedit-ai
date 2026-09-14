import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const origin = process.env.API_PROXY_ORIGIN || "http://localhost:8000";
  try {
    const cookie = request.headers.get("cookie") || "";
    const res = await fetch(`${origin}/api/auth/me`, {
      headers: { cookie },
      signal: AbortSignal.timeout(1000),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    // Backend offline: return clean 401 instead of proxy 500 error
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
}
