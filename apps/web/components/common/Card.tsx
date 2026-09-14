import { clsx } from "clsx";

/** Thin wrapper for the most common surface pattern in the app:
 * rounded-2xl + border-line + bg-panel. Not a variant system —
 * just stops repeating the same 3 classes in 20+ files. */
export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("rounded-2xl border border-line bg-panel", className)} {...props} />;
}
