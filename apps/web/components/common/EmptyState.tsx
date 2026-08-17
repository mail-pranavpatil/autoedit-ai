export function EmptyState({ title, body, action }: { title: string; body: string; action?: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-panel/50 p-10 text-center">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted">{body}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

export function LoadingSkeleton({ className = "h-24" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-white/5 ${className}`} />;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
      <p className="font-medium text-red-200">Something went wrong</p>
      <p className="mt-1 text-sm text-red-200/80">{message}</p>
      {onRetry && (
        <button className="mt-4 text-sm underline" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
