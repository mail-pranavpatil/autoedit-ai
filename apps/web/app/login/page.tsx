"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { toast } from "@/components/common/Toast";

function LoginForm() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const err = searchParams.get("error");
    if (err === "oauth" || err === "oauth_failed") {
      toast("Google sign in failed or was cancelled.", "err");
    }
  }, [searchParams]);

  async function signInWithGoogle() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
    if (error) toast("Google sign in failed to start.", "err");
  }

  return (
    <Card className="w-full max-w-md p-8">
      <h1 className="text-2xl font-semibold">AutoEdit AI</h1>
      <p className="mt-3 text-sm text-muted">
        Sign in with Google. Connect Drive separately afterward to import a folder of talking-head clips and get
        finished 9:16 reels.
      </p>
      <Button className="mt-8 w-full" onClick={signInWithGoogle}>
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
