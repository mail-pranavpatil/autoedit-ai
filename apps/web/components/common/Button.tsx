import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "danger" | "secondary" }) {
  const styles = {
    primary: "bg-accent text-ink hover:brightness-95",
    secondary: "bg-white/10 text-white hover:bg-white/15",
    ghost: "bg-transparent text-white hover:bg-white/10",
    danger: "bg-red-500/90 text-white hover:bg-red-500",
  };
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium disabled:opacity-40 disabled:pointer-events-none",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
