import { Link } from 'react-router-dom'
import { Dumbbell, Github } from 'lucide-react'

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-4 sm:px-6 h-16">
        <Link to="/" className="flex items-center gap-2 group">
          <Dumbbell className="w-5 h-5 text-green-500 group-hover:text-green-400 transition-colors" />
          <span className="font-mono font-bold text-lg text-white tracking-tight">
            FitHub
          </span>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          <Link
            to="/explore"
            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white transition-colors rounded-md hover:bg-zinc-800/50"
          >
            Workouts
          </Link>
          <Link
            to="/exercises"
            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white transition-colors rounded-md hover:bg-zinc-800/50"
          >
            Exercises
          </Link>
          <Link
            to="/docs"
            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white transition-colors rounded-md hover:bg-zinc-800/50"
          >
            Docs
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white transition-colors rounded-md hover:bg-zinc-800/50 flex items-center gap-1.5"
          >
            <Github className="w-4 h-4" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
          <Link
            to="/explore"
            className="ml-2 px-4 py-1.5 text-sm font-medium bg-green-600 hover:bg-green-500 text-white rounded-md transition-colors"
          >
            Get Started
          </Link>
        </nav>
      </div>
    </header>
  )
}
