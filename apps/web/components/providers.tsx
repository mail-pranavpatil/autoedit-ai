"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { usePathname, useRouter } from "next/navigation";
import { api, type User } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import { AppShell } from "@/components/layout/AppShell";
import { ToastHost } from "@/components/common/Toast";

// Mirrors the Supabase session into a cookie so plain <img>/<video>/<audio>
// tags to auth-gated media routes (thumbnails, source/output video, music)
// stay authenticated - there's no way to attach an Authorization header to a
// resource tag, and get_current_user reads this as a fallback.
function syncAuthCookie(session: Session | null) {
  if (session?.access_token) {
    const secure = location.protocol === "https:" ? "; secure" : "";
    document.cookie = `sb_access_token=${session.access_token}; path=/; samesite=lax${secure}`;
  } else {
    document.cookie = "sb_access_token=; path=/; max-age=0";
  }
}

const AuthContext = createContext<{
  user: User | null;
  refresh: () => Promise<void>;
}>({
  user: null,
  refresh: async () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  async function refresh() {
    try {
      const me = await api<User>("/api/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => syncAuthCookie(data.session));
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => syncAuthCookie(session));
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    refresh().finally(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (!user && pathname !== "/login") router.replace("/login");
    if (user && pathname === "/login") router.replace("/dashboard");
  }, [ready, user, pathname, router]);

  if (!ready) {
    return <div className="min-h-screen bg-ink p-8 text-muted">Loading AutoEdit AI…</div>;
  }

  if (pathname === "/login") {
    return (
      <AuthContext.Provider value={{ user, refresh }}>
        {children}
        <ToastHost />
      </AuthContext.Provider>
    );
  }

  if (!user) return null;

  const editor = pathname.includes("/editor");

  return (
    <AuthContext.Provider value={{ user, refresh }}>
      {editor ? children : <AppShell>{children}</AppShell>}
      <ToastHost />
    </AuthContext.Provider>
  );
}
