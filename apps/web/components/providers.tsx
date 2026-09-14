"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, type User } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { ToastHost } from "@/components/common/Toast";

const AuthContext = createContext<{
  user: User | null;
  refresh: () => Promise<void>;
  loginDemo: () => void;
}>({
  user: null,
  refresh: async () => {},
  loginDemo: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  function loginDemo() {
    if (typeof window !== "undefined") {
      localStorage.setItem("eren_demo_mode", "true");
      setUser({ id: "demo-1", email: "creator@eren.ai", name: "Eren Creator", driveConnected: true });
      router.replace("/dashboard");
    }
  }

  async function refresh() {
    if (typeof window !== "undefined" && localStorage.getItem("eren_demo_mode") === "true") {
      setUser({ id: "demo-1", email: "creator@eren.ai", name: "Eren Creator", driveConnected: true });
      return;
    }
    try {
      const me = await api<User>("/api/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    }
  }

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
      <AuthContext.Provider value={{ user, refresh, loginDemo }}>
        {children}
        <ToastHost />
      </AuthContext.Provider>
    );
  }

  if (!user) return null;

  const editor = pathname.includes("/editor");

  return (
    <AuthContext.Provider value={{ user, refresh, loginDemo }}>
      {editor ? children : <AppShell>{children}</AppShell>}
      <ToastHost />
    </AuthContext.Provider>
  );
}
