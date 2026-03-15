import { Link } from 'react-router-dom'
import { EXERCISES } from '../data/exercises'

export function ExercisesPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 sm:py-12">
      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
          Exercises
        </h1>
        <p className="text-zinc-400 text-lg">
          Browse all exercises with animations, tips, and variants.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {EXERCISES.map((exercise) => (
          <Link
            key={exercise.slug}
            to={`/exercise/${exercise.slug}`}
            className="group block bg-zinc-900 border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 hover:bg-zinc-900/80 transition-all"
          >
            {/* ASCII Preview */}
            <div className="bg-zinc-950 rounded-lg p-3 mb-4 overflow-hidden">
              <pre className="text-[8px] sm:text-[9px] leading-tight text-green-400 font-mono whitespace-pre overflow-x-auto">
                {exercise.animation_frames[0]}
              </pre>
            </div>

            <h3 className="font-semibold text-white group-hover:text-cyan-400 transition-colors mb-1">
              {exercise.name}
            </h3>

            <p className="text-sm text-zinc-400 line-clamp-2 mb-3">
              {exercise.description}
            </p>

            <div className="flex flex-wrap gap-1.5 mb-2">
              {exercise.muscle_groups.map((mg) => (
                <span
                  key={mg}
                  className="px-2 py-0.5 text-[10px] font-mono rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700/50 capitalize"
                >
                  {mg}
                </span>
              ))}
            </div>

            {exercise.variants.length > 0 && (
              <p className="text-xs text-zinc-600">
                {exercise.variants.length} variant{exercise.variants.length !== 1 ? 's' : ''}
              </p>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}
