import { Link } from 'react-router-dom'
import { ArrowRight, Terminal, BookOpen, Cpu, TrendingUp, Copy, Check } from 'lucide-react'
import { ActivityGrid } from '../components/ActivityGrid'
import { WebTerminal } from '../components/WebTerminal'
import { useState } from 'react'



const JSON_SNIPPET = `{
  "name": "Upper Body",
  "difficulty": "intermediate",
  "rounds": 3,
  "exercises": [
    {
      "name": "Push-Ups",
      "mode": "time",
      "value": 30,
      "muscle_groups": ["chest"]
    }
  ]
}`;

export function LandingPage() {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText('pip install gitfit');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div>
      {/* Hero */}
      <section className="py-12 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 w-full">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Try it live
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-4">
              <span className="text-cyan-400">GitHub</span>{' '}
              <span className="text-white">for Your Workouts</span>
            </h1>

            <p className="text-lg text-zinc-400 mb-6 max-w-2xl mx-auto leading-relaxed">
              Browse, fork, and customize workout plans like code repositories.
              This is a real GitFit session -- try it out.
            </p>

            <div className="flex flex-wrap gap-3 justify-center mb-10">
              <Link
                to="/explore"
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white font-medium rounded-lg transition-colors"
              >
                Explore Workouts
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 px-6 py-2.5 border border-zinc-700 hover:border-zinc-600 text-zinc-300 hover:text-white font-medium rounded-lg transition-all hover:bg-zinc-800/50"
              >
                <Terminal className="w-4 h-4" />
                Get Started
              </Link>
            </div>
          </div>

          {/* Live terminal */}
          <div className="relative max-w-4xl mx-auto">
            <WebTerminal />
            <div className="absolute -inset-4 bg-green-500/5 rounded-2xl -z-10 blur-2xl" />
          </div>
        </div>
      </section>

      {/* Activity Grid */}
      <section className="py-16 sm:py-24 border-t border-zinc-800/50">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-cyan-400 mb-3">
              Your Training Activity
            </h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              Every workout tracked, every streak visualized. Just like your contribution graph, but for gains.
            </p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 relative overflow-hidden">
            <ActivityGrid />
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="py-16 sm:py-24 border-t border-zinc-800/50">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-cyan-400 mb-3">
              Everything You Need
            </h2>
            <p className="text-zinc-400">
              Open source tools and formats to own your fitness journey.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {/* Workout Library */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4">
                <BookOpen className="w-5 h-5 text-cyan-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                Workout Library
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed">
                Browse and fork curated workout plans from the community.
                Every plan is open source and customizable to your level.
              </p>
            </div>

            {/* openWorkout Format */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center mb-4">
                <Terminal className="w-5 h-5 text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                openWorkout Format
              </h3>
              <p className="text-sm text-zinc-400 mb-3">
                A simple, open JSON format for workout definitions.
              </p>
              <div className="rounded-lg bg-zinc-950 border border-zinc-800 p-3 overflow-x-auto">
                <pre className="font-mono text-[11px] leading-relaxed">
                  <code>
                    <span className="text-zinc-500">{JSON_SNIPPET}</span>
                  </code>
                </pre>
              </div>
            </div>

            {/* AI-Powered Forking */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4">
                <Cpu className="w-5 h-5 text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                AI-Powered Forking
              </h3>
              <p className="text-sm text-zinc-400 mb-3">
                Fork any workout and let AI adapt it to your fitness level, equipment, and goals.
              </p>
              <div className="rounded-lg bg-zinc-950 border border-zinc-800 p-3">
                <code className="font-mono text-[11px] text-green-400">
                  $ app.py fork "arnold" --adapt "beginner"
                </code>
              </div>
            </div>

            {/* Level Up */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-4">
                <TrendingUp className="w-5 h-5 text-amber-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                Level Up
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed">
                Earn <span className="text-amber-400 font-medium">XP</span> for every workout, build{' '}
                <span className="text-green-400 font-medium">streaks</span>, and evolve your{' '}
                <span className="text-cyan-400 font-medium">Blobby</span> companion as you progress.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-16 sm:py-24 border-t border-zinc-800/50">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Ready to <span className="text-cyan-400">train</span>?
          </h2>
          <p className="text-zinc-400 mb-8 text-lg">
            Get started with the CLI in seconds.
          </p>

          <div className="inline-flex items-center gap-3 bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-3 font-mono text-sm">
            <span className="text-zinc-500">$</span>
            <span className="text-green-400">pip install gitfit</span>
            <button
              onClick={handleCopy}
              className="ml-2 p-1.5 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>

          <div className="mt-8">
            <Link
              to="/explore"
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white font-medium rounded-lg transition-colors"
            >
              Browse Workouts
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
