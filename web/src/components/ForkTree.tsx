interface ForkInfo {
  name: string;
  ai_adapted?: boolean;
}

interface ForkTreeProps {
  sourceName: string;
  sourceSlug: string;
  forks: ForkInfo[];
}

export function ForkTree({ sourceName, sourceSlug, forks }: ForkTreeProps) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      {/* Source node */}
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2.5 h-2.5 rounded-full bg-green-500 flex-shrink-0" />
        <span className="text-sm font-medium text-white">{sourceName}</span>
        <span className="text-xs text-zinc-500 font-mono">{sourceSlug}</span>
      </div>

      {/* Fork nodes */}
      {forks.length > 0 ? (
        <div className="ml-1 border-l border-zinc-700 pl-4 space-y-2">
          {forks.map((fork, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500 flex-shrink-0" />
              <span className="text-sm text-zinc-300">{fork.name}</span>
              {fork.ai_adapted && (
                <span className="px-1.5 py-0.5 text-[10px] rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">
                  AI-adapted
                </span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-zinc-500 ml-5">No community forks yet. Be the first!</p>
      )}
    </div>
  )
}
