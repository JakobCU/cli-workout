import { Link } from 'react-router-dom'
import { Dumbbell, Github, ChevronDown, User, Settings, LogOut } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { useState, useRef, useEffect } from 'react'

export function Header() {
  const { user, isAuthenticated, logout } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-4 sm:px-6 h-16">
        <Link to="/" className="flex items-center gap-2 group">
          <Dumbbell className="w-5 h-5 text-green-500 group-hover:text-green-400 transition-colors" />
          <span className="font-mono font-bold text-lg text-white tracking-tight">
            GitFitHub
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

          {isAuthenticated && user ? (
            <div className="relative ml-2" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-300 hover:text-white rounded-md hover:bg-zinc-800/50 transition-colors"
              >
                <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center">
                  <span className="text-xs font-medium text-green-400">
                    {(user.name || user.username || '?')[0].toUpperCase()}
                  </span>
                </div>
                <span className="hidden sm:inline">{user.username}</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 mt-1 w-48 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl py-1 z-50">
                  <Link
                    to={`/user/${user.username}`}
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:text-white hover:bg-zinc-800"
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </Link>
                  <Link
                    to="/settings"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:text-white hover:bg-zinc-800"
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </Link>
                  <hr className="border-zinc-800 my-1" />
                  <button
                    onClick={() => { logout(); setDropdownOpen(false) }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-zinc-400 hover:text-red-400 hover:bg-zinc-800"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                to="/login"
                className="ml-2 px-3 py-1.5 text-sm text-zinc-300 hover:text-white transition-colors rounded-md hover:bg-zinc-800/50"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-1.5 text-sm font-medium bg-green-600 hover:bg-green-500 text-white rounded-md transition-colors"
              >
                Get Started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
