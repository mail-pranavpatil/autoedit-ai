"use client";

import { createContext, useContext, useState, useCallback } from "react";

type Toast = { id: number; message: string; kind?: "ok" | "err" };

const Ctx = createContext<(message: string, kind?: "ok" | "err") => void>(() => {});

let _push: (message: string, kind?: "ok" | "err") => void = () => {};

export function toast(message: string, kind: "ok" | "err" = "ok") {
  _push(message, kind);
}

export function useToast() {
  return useContext(Ctx);
}

export function ToastHost() {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((message: string, kind: "ok" | "err" = "ok") => {
    const id = Date.now();
    setItems((prev) => [...prev, { id, message, kind }]);
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);
  _push = push;

  return (
    <Ctx.Provider value={push}>
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={`rounded-xl px-4 py-3 text-sm shadow-lg ${
              t.kind === "err" ? "bg-red-500/90 text-white" : "bg-accent text-ink"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
