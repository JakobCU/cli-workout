import { useParams, Link } from 'react-router-dom'
import { Clock, RotateCcw, Dumbbell, ChevronRight, Copy, Check, ArrowLeft, GitFork } from 'lucide-react'
import { getWorkoutBySlug } from '../data/workouts'
import { getExerciseBySlug } from '../data/exercises'
import { DifficultyBadge } from '../components/DifficultyBadge'
import { ForkTree } from '../components/ForkTree'
import { useState, useMemo } from 'react'

function exerciseSlug(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '-');
}

export function WorkoutDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const workout = slug ? getWorkoutBySlug(slug) : undefined;
  const [copied, setCopied] = useState<string | null>(null);

  const muscleGroupCounts = useMemo(() => {
    if (!workout) return [];
    const counts: Record<string, number> = {};
    workout.exercises.forEach((ex) => {
      ex.muscle_groups.forEach((mg) => {
        counts[mg] = (counts[mg] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
  }, [workout]);

  const maxMuscleCount = muscleGroupCounts.length > 0
    ? Math.max(...muscleGroupCounts.map(m => m.count))
    : 1;

  function handleCopy(text: string, id: string) {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  }

  if (!workout) {
    return (
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-16 text-center">
        <h1 className="text-2xl font-bold text-white mb-4">Workout not found</h1>
        <p className="text-zinc-400 mb-6">
          The workout you're looking for doesn't exist.
        </p>
        <Link to="/explore" className="text-green-400 hover:text-green-300 transition-colors">
          Browse all workouts
        </Link>

      </div>
    );
  }

  const forkCmd = `python app.py fork "${workout.id}"`;
  const adaptCmd = `python app.py fork "${workout.id}" --adapt "beginner, bodyweight"`;

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 sm:py-12">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-zinc-500 mb-6">
        <Link to="/explore" className="hover:text-zinc-300 transition-colors flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          Workouts
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-zinc-300">{workout.name}</span>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-start gap-3 mb-3">
          <h1 className="text-3xl sm:text-4xl font-bold text-white">
            {workout.name}
          </h1>
          <DifficultyBadge difficulty={workout.difficulty} size="md" />
        </div>

        <p className="text-zinc-400 mb-1 text-sm font-mono">
          <span className="text-zinc-500">by</span>{' '}
          <span className="text-cyan-400">{workout.id.split('/')[0]}</span>
        </p>

        <p className="text-zinc-400 text-lg mb-6 max-w-2xl">
          {workout.description}
        </p>

        {/* Stats */}
        <div className="flex flex-wrap gap-4 sm:gap-6">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-zinc-500" />
            <span className="text-zinc-400">
              <span className="text-white font-medium">{workout.estimated_duration_min}</span> min
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <RotateCcw className="w-4 h-4 text-zinc-500" />
            <span className="text-zinc-400">
              <span className="text-white font-medium">{workout.rounds}</span> rounds
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Dumbbell className="w-4 h-4 text-zinc-500" />
            <span className="text-zinc-400">
              <span className="text-white font-medium">{workout.exercises.length}</span> exercises
            </span>
          </div>
          {workout.fork_count > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <GitFork className="w-4 h-4 text-zinc-500" />
              <span className="text-zinc-400">
                <span className="text-white font-medium">{workout.fork_count}</span> forks
              </span>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            Equipment: <span className="text-white font-medium capitalize">{workout.equipment.join(', ')}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Exercise Table */}
        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold text-cyan-400 mb-4">Exercises</h2>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-500 text-left">
                    <th className="px-4 py-3 font-medium w-10">#</th>
                    <th className="px-4 py-3 font-medium">Exercise</th>
                    <th className="px-4 py-3 font-medium">Mode</th>
                    <th className="px-4 py-3 font-medium">Value</th>
                    <th className="px-4 py-3 font-medium hidden sm:table-cell">Muscle Groups</th>
                  </tr>
                </thead>
                <tbody>
                  {workout.exercises.map((ex, i) => (
                    <tr
                      key={i}
                      className="border-b border-zinc-800/50 last:border-b-0 hover:bg-zinc-800/30 transition-colors"
                    >
                      <td className="px-4 py-3 text-zinc-600 font-mono text-xs">
                        {i + 1}
                      </td>
                      <td className="px-4 py-3 font-medium">
                        {getExerciseBySlug(exerciseSlug(ex.name)) ? (
                          <Link
                            to={`/exercise/${exerciseSlug(ex.name)}`}
                            className="text-yellow-400 hover:text-yellow-300 underline decoration-zinc-700 hover:decoration-yellow-400/50 transition-colors"
                          >
                            {ex.name}
                          </Link>
                        ) : (
                          <span className="text-yellow-400">{ex.name}</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex px-2 py-0.5 text-xs rounded bg-zinc-800 text-zinc-400 font-mono">
                          {ex.mode}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-white font-mono">
                        {ex.value}{ex.mode === 'time' ? 's' : ''}
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <div className="flex flex-wrap gap-1">
                          {ex.muscle_groups.map((mg) => (
                            <span
                              key={mg}
                              className="px-1.5 py-0.5 text-[10px] rounded bg-zinc-800 text-zinc-500 capitalize"
                            >
                              {mg}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Muscle Group Chart */}
          <div>
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">Muscle Groups</h2>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-2.5">
              {muscleGroupCounts.map(({ name, count }) => (
                <div key={name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-zinc-400 capitalize">{name}</span>
                    <span className="text-xs text-zinc-600 font-mono">{count}</span>
                  </div>
                  <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full transition-all"
                      style={{ width: `${(count / maxMuscleCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fork CTA */}
          <div>
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">Fork This Workout</h2>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
              <div>
                <p className="text-xs text-zinc-500 mb-1.5">Clone as-is:</p>
                <div className="flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2">
                  <code className="text-xs text-green-400 font-mono flex-1 overflow-x-auto">
                    {forkCmd}
                  </code>
                  <button
                    onClick={() => handleCopy(forkCmd, 'fork')}
                    className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors flex-shrink-0"
                  >
                    {copied === 'fork' ? (
                      <Check className="w-3.5 h-3.5 text-green-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <p className="text-xs text-zinc-500 mb-1.5">AI-adapt for you:</p>
                <div className="flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2">
                  <code className="text-xs text-green-400 font-mono flex-1 overflow-x-auto">
                    {adaptCmd}
                  </code>
                  <button
                    onClick={() => handleCopy(adaptCmd, 'adapt')}
                    className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors flex-shrink-0"
                  >
                    {copied === 'adapt' ? (
                      <Check className="w-3.5 h-3.5 text-green-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Fork Tree */}
          <div>
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">Fork Tree</h2>
            <ForkTree
              sourceName={workout.name}
              sourceSlug={workout.id}
              forks={[
                { name: `My ${workout.name}`, ai_adapted: false },
                { name: `${workout.name} Lite`, ai_adapted: true },
              ]}
            />
          </div>

          {/* Tags */}
          <div>
            <h3 className="text-sm font-medium text-zinc-400 mb-2">Tags</h3>
            <div className="flex flex-wrap gap-1.5">
              {workout.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 text-xs font-mono rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700/50"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
