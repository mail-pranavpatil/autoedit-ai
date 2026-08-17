"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { useState } from "react";
import { useAuth } from "@/components/providers";
import { API_URL, api } from "@/lib/api";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/assets", label: "Assets" },
  { href: "/style", label: "Style Profile" },
  { href: "/settings", label: "Settings" },
];

const foot = [
  { href: "/help", label: "Help" },
  { href: "/system", label: "System Status" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  }

  const Nav = () => (
    <>
      <div className="px-4 py-5 text-lg font-semibold tracking-tight">AutoEdit AI</div>
      <nav className="flex-1 space-y-1 px-2">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setOpen(false)}
            className={clsx(
              "block rounded-xl px-3 py-2 text-sm",
              pathname.startsWith(item.href) ? "bg-white/10 text-white" : "text-muted hover:bg-white/5 hover:text-white"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="space-y-1 px-2 pb-3">
        {foot.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setOpen(false)}
            className={clsx(
              "block rounded-xl px-3 py-2 text-sm",
              pathname.startsWith(item.href) ? "bg-white/10 text-white" : "text-muted hover:bg-white/5"
            )}
          >
            {item.label}
          </Link>
        ))}
      </div>
      <div className="border-t border-line p-4">
        <div className="text-sm">{user?.name || user?.email}</div>
        <div className="text-xs text-muted">{user?.email}</div>
        <button onClick={logout} className="mt-3 text-xs text-muted underline">
          Log out
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-ink lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="hidden min-h-screen flex-col border-r border-line bg-panel lg:flex">
        <Nav />
      </aside>
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b border-line px-4 py-3 lg:px-8">
          <button className="rounded-lg px-2 py-1 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            Menu
          </button>
          <div className="text-sm text-muted">Upload raw videos. AutoEdit AI handles the editing.</div>
          <a href={`${API_URL}/health`} className="text-xs text-muted" target="_blank" rel="noreferrer">
            API
          </a>
        </header>
        <main className="flex-1 p-4 lg:p-8">{children}</main>
      </div>
      {open && (
        <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setOpen(false)}>
          <div className="flex h-full w-64 flex-col bg-panel" onClick={(e) => e.stopPropagation()}>
            <Nav />
          </div>
        </div>
      )}
    </div>
  );
}
