import { Link } from 'react-router-dom'
import { Clock, RotateCcw, Dumbbell } from 'lucide-react'
import { DifficultyBadge } from './DifficultyBadge'
import { ForkBadge } from './ForkBadge'
import type { OpenWorkout } from '../data/workouts'
import { getSlug } from '../data/workouts'

interface WorkoutCardProps {
  workout: OpenWorkout;
}

export function WorkoutCard({ workout }: WorkoutCardProps) {
  return (
    <Link
      to={`/workout/${getSlug(workout)}`}
      className="group block bg-zinc-900 border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 hover:bg-zinc-900/80 transition-all"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-semibold text-white group-hover:text-cyan-400 transition-colors line-clamp-1">
          {workout.name}
        </h3>
        <DifficultyBadge difficulty={workout.difficulty} />
      </div>

      <p className="text-sm text-zinc-400 line-clamp-2 mb-4">
        {workout.description}
      </p>

      <div className="flex items-center gap-4 text-xs text-zinc-500">
        <span className="flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          {workout.estimated_duration_min}min
        </span>
        <span className="flex items-center gap-1">
          <RotateCcw className="w-3.5 h-3.5" />
          {workout.rounds}R
        </span>
        <span className="flex items-center gap-1">
          <Dumbbell className="w-3.5 h-3.5" />
          {workout.exercises.length}ex
        </span>
        {workout.fork_count > 0 && <ForkBadge count={workout.fork_count} />}
      </div>

      <div className="flex flex-wrap gap-1.5 mt-3">
        {workout.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="px-2 py-0.5 text-[10px] font-mono rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700/50"
          >
            {tag}
          </span>
        ))}
        {workout.tags.length > 3 && (
          <span className="px-2 py-0.5 text-[10px] font-mono text-zinc-600">
            +{workout.tags.length - 3}
          </span>
        )}
      </div>
    </Link>
  )
}
