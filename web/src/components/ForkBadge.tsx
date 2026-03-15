import { GitFork } from 'lucide-react'

interface ForkBadgeProps {
  count: number;
}

export function ForkBadge({ count }: ForkBadgeProps) {
  if (count <= 0) return null;

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700/50">
      <GitFork className="w-3 h-3" />
      {count}
    </span>
  )
}
