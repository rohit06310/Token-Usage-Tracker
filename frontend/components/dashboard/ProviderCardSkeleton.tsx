"use client";

export function ProviderCardSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-700/50 bg-slate-800/60 p-5">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-slate-700/60" />
          <div className="space-y-2">
            <div className="h-4 w-24 rounded bg-slate-700/60" />
            <div className="h-3 w-16 rounded bg-slate-700/40" />
          </div>
        </div>
        <div className="h-5 w-24 rounded-full bg-slate-700/60" />
      </div>

      {/* Stats */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="space-y-2 rounded-lg bg-slate-700/30 p-2.5">
            <div className="mx-auto h-3.5 w-3.5 rounded bg-slate-600/60" />
            <div className="mx-auto h-4 w-10 rounded bg-slate-600/60" />
            <div className="mx-auto h-3 w-14 rounded bg-slate-600/40" />
          </div>
        ))}
      </div>

      {/* 30d cost bar */}
      <div className="mb-4 h-9 rounded-lg bg-slate-700/30" />

      {/* Quota bars */}
      <div className="space-y-3 border-t border-slate-700/50 pt-4">
        {[0, 1].map((i) => (
          <div key={i} className="space-y-1.5">
            <div className="flex justify-between">
              <div className="h-3 w-8 rounded bg-slate-700/60" />
              <div className="h-3 w-10 rounded bg-slate-700/60" />
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-700/60" />
          </div>
        ))}
      </div>
    </div>
  );
}
