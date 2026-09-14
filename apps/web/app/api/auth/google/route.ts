import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const origin = process.env.API_PROXY_ORIGIN || "http://localhost:8000";
  try {
    const res = await fetch(`${origin}/health`, { signal: AbortSignal.timeout(1000) });
    if (res.ok) {
      return NextResponse.redirect(`${origin}/api/auth/google`);
    }
  } catch {
    // Backend is offline — redirect back to login with notice
    const url = new URL(request.url);
    url.pathname = "/login";
    url.searchParams.set("error", "backend_offline");
    return NextResponse.redirect(url);
  }
  return NextResponse.redirect(`${origin}/api/auth/google`);
}
