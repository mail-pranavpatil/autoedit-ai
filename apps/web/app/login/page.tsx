"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { API_URL } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { toast } from "@/components/common/Toast";

function LoginForm() {
  const searchParams = useSearchParams();

  useEffect(() => {
    if (searchParams.get("error") === "oauth") {
      toast("Google sign in failed or was cancelled.", "err");
    }
  }, [searchParams]);

  return (
    <Card className="w-full max-w-md p-8">
      <h1 className="text-2xl font-semibold">AutoEdit AI</h1>
      <p className="mt-3 text-sm text-muted">
        Sign in with Google. The same account connects Drive so you can import a folder of talking-head clips and get
        finished 9:16 reels.
      </p>
      <Button className="mt-8 w-full" onClick={() => (window.location.href = `${API_URL}/api/auth/google`)}>
        Continue with Google
      </Button>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-ink p-6">
      <Suspense fallback={<Card className="w-full max-w-md p-8 text-center text-muted">Loading…</Card>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
