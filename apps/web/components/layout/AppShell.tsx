"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clsx } from "clsx";
import { useState } from "react";
import { useAuth } from "@/components/providers";
import { api } from "@/lib/api";
import {
  Home,
  FolderOpen,
  PlusCircle,
  Upload,
  Palette,
  Package,
  Settings,
  HelpCircle,
  Activity,
  LogOut,
  User,
} from "lucide-react";

const tabs = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/projects", label: "Projects", icon: FolderOpen },
  { href: "/create", label: "Create", icon: PlusCircle },
  { href: "/youtube", label: "Publish", icon: Upload },
  { href: "/style", label: "Style", icon: Palette },
];

const profileLinks = [
  { href: "/assets", label: "Assets", icon: Package },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/help", label: "Help", icon: HelpCircle },
  { href: "/system", label: "System Status", icon: Activity },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  }

  return (
    <div className="flex min-h-screen flex-col bg-ink pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)]">
      <header className="flex items-center justify-between border-b border-line px-4 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <div className="text-lg font-semibold tracking-tight">AutoEdit AI</div>
        <button
          className="flex h-11 items-center gap-1.5 rounded-xl px-3 py-2 text-sm text-muted transition-colors duration-150 hover:bg-white/5 hover:text-white"
          onClick={() => setProfileOpen(true)}
          aria-label="Open profile menu"
        >
          <User className="h-4 w-4" />
          Profile
        </button>
      </header>

      <main className="flex-1 p-4 pb-24">{children}</main>

      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-line bg-panel pb-[env(safe-area-inset-bottom)]">
        {tabs.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={clsx(
                "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-xs transition-colors duration-150",
                active ? "text-accent" : "text-muted hover:text-white"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Profile sheet backdrop */}
      {profileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 transition-opacity duration-200"
          onClick={() => setProfileOpen(false)}
        />
      )}

      {/* Profile bottom sheet */}
      <div
        className={clsx(
          "fixed inset-x-0 bottom-0 z-40 transform transition-transform duration-300 ease-out",
          profileOpen ? "translate-y-0" : "translate-y-full"
        )}
      >
        <div className="w-full rounded-t-2xl bg-panel pb-[env(safe-area-inset-bottom)]" onClick={(e) => e.stopPropagation()}>
          <div className="border-b border-line p-4">
            <div className="text-sm">{user?.name || user?.email}</div>
            <div className="text-xs text-muted">{user?.email}</div>
          </div>
          <div className="p-2">
            {profileLinks.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted transition-colors duration-150 hover:bg-white/5 hover:text-white"
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
            <button
              onClick={logout}
              className="mt-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-red-300 transition-colors duration-150 hover:bg-white/5"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
