"use client";

import { API_URL } from "@/lib/api";
import { Button } from "@/components/common/Button";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-ink p-6">
      <div className="w-full max-w-md rounded-2xl border border-line bg-panel p-8">
        <h1 className="text-2xl font-semibold">AutoEdit AI</h1>
        <p className="mt-3 text-sm text-muted">
          Sign in with Google. The same account connects Drive so you can import a folder of talking-head clips and get
          finished 9:16 reels.
        </p>
        <div style={{margin:'12px 0', color: '#ff4a4a', fontFamily: 'monospace', fontSize:'small'}}>
          API_URL at runtime: <span id="api-url-val">{API_URL}</span>
        </div>
        <Button className="mt-8 w-full" onClick={() => (window.location.href = `${API_URL}/api/auth/google`)}>
          Continue with Google
        </Button>
      </div>
    </div>
  );
}
