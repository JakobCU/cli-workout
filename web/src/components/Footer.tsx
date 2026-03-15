import { Dumbbell, Github } from 'lucide-react'
import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Dumbbell className="w-4 h-4 text-green-500" />
              <span className="font-mono font-bold text-white">FitHub</span>
            </div>
            <p className="text-sm text-zinc-500">
              GitHub for your workouts. Open source fitness tracking with the openWorkout format.
            </p>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Links
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/explore" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors">
                  Explore Workouts
                </Link>
              </li>
              <li>
                <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors flex items-center gap-1.5">
                  <Github className="w-3.5 h-3.5" />
                  GitHub
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Format
            </h4>
            <p className="text-sm text-zinc-500">
              Built with <span className="font-mono text-green-500">openWorkout v1.0</span>
            </p>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-zinc-800/50 text-center">
          <p className="text-xs text-zinc-600">
            &copy; {new Date().getFullYear()} FitHub. Train hard, commit often.
          </p>
        </div>
      </div>
    </footer>
  )
}
