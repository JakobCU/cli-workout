import { Link } from 'react-router-dom'
import { ArrowRight, Terminal, BookOpen, Cpu, TrendingUp, Copy, Check } from 'lucide-react'
import { ActivityGrid } from '../components/ActivityGrid'
import { useState } from 'react'

const BLOBBY_ART = `        \\\\  /
     .-''''-.
    / o    o \\\\
   |  (~~~~)  |
    \\\\ \`----' /
     '------'
        ||
       /  \\\\
      /    \\\\
    _|_    _|_`;

const CLI_LINES = [
  { type: 'input' as const, text: '$ python app.py fork "fithub/arnold-golden-era" --adapt "beginner, bodyweight"' },
  { type: 'blank' as const, text: '' },
  { type: 'info' as const, text: '  AI Fork: adapting \'Arnold Golden Era\'...' },
  { type: 'blank' as const, text: '' },
  { type: 'detail' as const, text: '  ORIGINAL: Arnold Golden Era (4R, 7ex, ~29min)' },
  { type: 'success' as const, text: '  ADAPTED:  Arnold Lite (2R, 5ex, ~15min)' },
  { type: 'blank' as const, text: '' },
  { type: 'success' as const, text: '  Forked successfully!' },
];

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
    navigator.clipboard.writeText('pip install fithub-cli');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div>
      {/* Hero */}
      <section className="min-h-[calc(100vh-4rem)] flex items-center">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-16 sm:py-24 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left - Text */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                openWorkout v1.0
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
                <span className="text-cyan-400">GitHub</span>{' '}
                <span className="text-white">for Your</span>
                <br />
                <span className="text-white">Workouts</span>
              </h1>

              <p className="text-lg text-zinc-400 mb-8 max-w-lg leading-relaxed">
                Browse, fork, and customize workout plans like code repositories.
                Track your training with an open format that puts you in control.
              </p>

              <div className="flex flex-wrap gap-3">
                <Link
                  to="/explore"
                  className="inline-flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white font-medium rounded-lg transition-colors"
                >
                  Explore Workouts
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-2.5 border border-zinc-700 hover:border-zinc-600 text-zinc-300 hover:text-white font-medium rounded-lg transition-all hover:bg-zinc-800/50"
                >
                  <Terminal className="w-4 h-4" />
                  View CLI
                </a>
              </div>
            </div>

            {/* Right - Blobby terminal */}
            <div className="relative">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden shadow-2xl shadow-green-500/5">
                {/* Terminal header */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
                  <div className="w-3 h-3 rounded-full bg-red-500/70" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
                  <div className="w-3 h-3 rounded-full bg-green-500/70" />
                  <span className="ml-2 text-xs text-zinc-600 font-mono">blobby.sh</span>
                </div>
                {/* Terminal content */}
                <div className="p-6 font-mono text-sm">
                  <pre className="text-green-400 leading-relaxed whitespace-pre">{BLOBBY_ART}</pre>
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <span className="text-zinc-500">{'>'} </span>
                    <span className="text-cyan-400">blobby</span>
                    <span className="text-zinc-400"> says: </span>
                    <span className="text-yellow-400">"Let's get training!"</span>
                    <span className="inline-block w-2 h-4 bg-green-400 ml-1 animate-pulse" />
                  </div>
                </div>
              </div>
              {/* Glow effect */}
              <div className="absolute -inset-4 bg-green-500/5 rounded-2xl -z-10 blur-2xl" />
            </div>
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

      {/* CLI Demo */}
      <section className="py-16 sm:py-24 border-t border-zinc-800/50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-cyan-400 mb-3">
              Powerful CLI
            </h2>
            <p className="text-zinc-400">
              Train from your terminal. Fork, adapt, and track workouts with simple commands.
            </p>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden shadow-2xl shadow-green-500/5">
            {/* Terminal header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
              <div className="w-3 h-3 rounded-full bg-red-500/70" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
              <div className="w-3 h-3 rounded-full bg-green-500/70" />
              <span className="ml-2 text-xs text-zinc-600 font-mono">terminal</span>
            </div>
            {/* Terminal content */}
            <div className="p-6 font-mono text-sm space-y-0.5">
              {CLI_LINES.map((line, i) => (
                <div key={i} className="leading-relaxed">
                  {line.type === 'input' && (
                    <span className="text-zinc-300">{line.text}</span>
                  )}
                  {line.type === 'info' && (
                    <span className="text-cyan-400">{line.text}</span>
                  )}
                  {line.type === 'detail' && (
                    <span className="text-zinc-400">{line.text}</span>
                  )}
                  {line.type === 'success' && (
                    <span className="text-green-400">{line.text}</span>
                  )}
                  {line.type === 'blank' && (
                    <span>&nbsp;</span>
                  )}
                </div>
              ))}
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
            <span className="text-green-400">pip install fithub-cli</span>
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
