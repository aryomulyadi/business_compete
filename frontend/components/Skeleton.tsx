export function SkeletonCard() {
  return (
    <div className="card p-4 space-y-3 animate-fade-in">
      <div className="h-5 w-2/3 shimmer rounded" />
      <div className="h-3 w-full shimmer rounded" />
      <div className="h-3 w-4/5 shimmer rounded" />
      <div className="flex gap-2 pt-1">
        <div className="h-8 w-20 shimmer rounded-lg" />
        <div className="h-8 w-20 shimmer rounded-lg" />
      </div>
    </div>
  )
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2 animate-fade-in">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 shimmer rounded"
          style={{ width: `${Math.max(40, 100 - i * 15)}%` }}
        />
      ))}
    </div>
  )
}

export function SkeletonPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="h-8 w-1/3 shimmer rounded-lg" />
      <div className="h-4 w-1/2 shimmer rounded" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  )
}

export function SkeletonTable() {
  return (
    <div className="space-y-3 animate-fade-in">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="card p-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2 flex-1">
              <div className="h-4 w-2/5 shimmer rounded" />
              <div className="h-3 w-1/4 shimmer rounded" />
            </div>
            <div className="flex gap-2">
              <div className="h-7 w-14 shimmer rounded-lg" />
              <div className="h-7 w-10 shimmer rounded-lg" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
