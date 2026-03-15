import { useParams, Link } from 'react-router-dom'
import { ChevronRight, ArrowLeft, Clock, GitBranch } from 'lucide-react'
import { getExerciseBySlug } from '../data/exercises'
import { useState, useEffect } from 'react'

export function ExerciseDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const exercise = slug ? getExerciseBySlug(slug) : undefined;
  const [frameIndex, setFrameIndex] = useState(0);

  useEffect(() => {
    if (!exercise) return;
    const interval = setInterval(() => {
      setFrameIndex((prev) => (prev + 1) % exercise.animation_frames.length);
    }, 500);
    return () => clearInterval(interval);
  }, [exercise]);

  if (!exercise) {
    return (
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-16 text-center">
        <h1 className="text-2xl font-bold text-white mb-4">Exercise not found</h1>
        <Link to="/exercises" className="text-green-400 hover:text-green-300 transition-colors">
          Browse all exercises
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 sm:py-12">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-zinc-500 mb-6">
        <Link to="/exercises" className="hover:text-zinc-300 transition-colors flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          Exercises
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-zinc-300">{exercise.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {/* Header */}
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            {exercise.name}
          </h1>
          <p className="text-zinc-400 text-lg mb-6">
            {exercise.description}
          </p>

          {/* Animated ASCII Preview */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-cyan-400">Animation Preview</h2>
              <span className="text-xs text-zinc-600 font-mono">
                frame {frameIndex + 1}/{exercise.animation_frames.length}
              </span>
            </div>
            <pre className="text-xs sm:text-sm leading-tight text-green-400 font-mono whitespace-pre overflow-x-auto min-h-[140px]">
              {exercise.animation_frames[frameIndex]}
            </pre>
          </div>

          {/* Tips */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-cyan-400 mb-3">Tips</h2>
            <ul className="space-y-2">
              {exercise.tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-2 text-zinc-300">
                  <span className="text-green-500 mt-0.5 flex-shrink-0">-</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>

          {/* Variants */}
          {exercise.variants.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-cyan-400 mb-4 flex items-center gap-2">
                <GitBranch className="w-5 h-5" />
                Variants
              </h2>
              <div className="space-y-3">
                {exercise.variants.map((variant) => (
                  <div
                    key={variant.slug}
                    className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
                  >
                    <h3 className="font-semibold text-white mb-1">{variant.name}</h3>
                    <p className="text-sm text-zinc-400 mb-2">{variant.description}</p>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1 text-xs text-zinc-500">
                        <Clock className="w-3 h-3" />
                        {variant.default_value}s
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {variant.muscle_groups.map((mg) => (
                          <span
                            key={mg}
                            className="px-1.5 py-0.5 text-[10px] rounded bg-zinc-800 text-zinc-500 capitalize"
                          >
                            {mg}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Stats */}
          <div>
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">Details</h2>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Default Mode</span>
                <span className="text-white font-mono">{exercise.default_mode}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Default Value</span>
                <span className="text-white font-mono">
                  {exercise.default_value}{exercise.default_mode === 'time' ? 's' : ' reps'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Variants</span>
                <span className="text-white font-mono">{exercise.variants.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Frames</span>
                <span className="text-white font-mono">{exercise.animation_frames.length}</span>
              </div>
            </div>
          </div>

          {/* Muscle Groups */}
          <div>
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">Muscle Groups</h2>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <div className="flex flex-wrap gap-1.5">
                {exercise.muscle_groups.map((mg) => (
                  <span
                    key={mg}
                    className="px-2.5 py-1 text-xs font-mono rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700/50 capitalize"
                  >
                    {mg}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Use in workout */}
          <div>
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">Use in Workout</h2>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <p className="text-xs text-zinc-500 mb-2">Add to a custom workout:</p>
              <pre className="text-xs text-green-400 font-mono bg-zinc-950 rounded-lg p-3 overflow-x-auto">
{`{
  "name": "${exercise.name}",
  "mode": "${exercise.default_mode}",
  "value": ${exercise.default_value}
}`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
