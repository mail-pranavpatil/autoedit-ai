import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

export function Button({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger" | "secondary";
  size?: "sm" | "md" | "lg";
}) {
  const styles = {
    primary: "bg-accent text-ink hover:brightness-95",
    secondary: "bg-white/10 text-white hover:bg-white/15",
    ghost: "bg-transparent text-white hover:bg-white/10",
    danger: "bg-red-500/90 text-white hover:bg-red-500",
  };
  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs min-h-[36px]",
    md: "px-4 py-2.5 text-sm min-h-[44px]",
    lg: "px-6 py-3 text-base min-h-[48px]",
  };
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl font-medium transition-colors duration-150 ease-out disabled:opacity-40 disabled:pointer-events-none",
        styles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    />
  );
}
