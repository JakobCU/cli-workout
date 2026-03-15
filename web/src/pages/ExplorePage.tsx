import { useState, useMemo } from 'react'
import { Search } from 'lucide-react'
import { WORKOUTS } from '../data/workouts'
import { WorkoutCard } from '../components/WorkoutCard'

const DIFFICULTY_FILTERS = ['all', 'beginner', 'intermediate', 'advanced'] as const;
type DifficultyFilter = typeof DIFFICULTY_FILTERS[number];

const filterColors: Record<DifficultyFilter, { active: string; inactive: string }> = {
  all: { active: 'bg-zinc-700 text-white', inactive: 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300' },
  beginner: { active: 'bg-green-600/20 text-green-400 border-green-500/30', inactive: 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300' },
  intermediate: { active: 'bg-yellow-600/20 text-yellow-400 border-yellow-500/30', inactive: 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300' },
  advanced: { active: 'bg-red-600/20 text-red-400 border-red-500/30', inactive: 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300' },
};

export function ExplorePage() {
  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('all');

  const filtered = useMemo(() => {
    return WORKOUTS.filter((w) => {
      if (difficulty !== 'all' && w.difficulty !== difficulty) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          w.name.toLowerCase().includes(q) ||
          w.description.toLowerCase().includes(q) ||
          w.tags.some((t) => t.includes(q)) ||
          w.muscle_groups.some((m) => m.includes(q))
        );
      }
      return true;
    });
  }, [search, difficulty]);

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-12 sm:py-16">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-cyan-400 mb-2">
          Explore Workouts
        </h1>
        <p className="text-zinc-400">
          <span className="text-zinc-300 font-medium">{WORKOUTS.length}</span> open source workout plans ready to fork
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        {/* Difficulty Pills */}
        <div className="flex gap-2 flex-wrap">
          {DIFFICULTY_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setDifficulty(f)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg border border-transparent transition-all capitalize ${
                difficulty === f ? filterColors[f].active : filterColors[f].inactive
              }`}
            >
              {f === 'all' ? 'All' : f}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative sm:ml-auto">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search workouts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-64 pl-9 pr-4 py-2 text-sm bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
          />
        </div>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-zinc-500 text-lg">No workouts match your filters.</p>
          <button
            onClick={() => { setSearch(''); setDifficulty('all'); }}
            className="mt-3 text-sm text-green-400 hover:text-green-300 transition-colors"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((workout) => (
            <WorkoutCard key={workout.id} workout={workout} />
          ))}
        </div>
      )}
    </div>
  );
}
