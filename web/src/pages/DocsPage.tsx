import { useState } from 'react'
import { BookOpen, Bot, Terminal, Copy, Check, Dumbbell, Trophy, TrendingUp, Zap, GitFork } from 'lucide-react'

type Tab = 'humans' | 'agents'

function CodeBlock({ code, language = '' }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group rounded-lg bg-zinc-950 border border-zinc-800 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/50">
        <span className="text-[11px] text-zinc-500 font-mono">{language}</span>
        <button
          onClick={handleCopy}
          className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
          title="Copy"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-[13px] leading-relaxed font-mono text-zinc-300">
        <code>{code}</code>
      </pre>
    </div>
  )
}

function Section({ icon: Icon, title, children, color = 'cyan' }: {
  icon: React.ElementType
  title: string
  children: React.ReactNode
  color?: string
}) {
  const colorMap: Record<string, string> = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    green: 'text-green-400 bg-green-500/10 border-green-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    red: 'text-red-400 bg-red-500/10 border-red-500/20',
  }
  const c = colorMap[color] || colorMap.cyan

  return (
    <div className="mb-12">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${c}`}>
          <Icon className="w-4 h-4" />
        </div>
        <h2 className="text-xl font-bold text-white">{title}</h2>
      </div>
      <div className="text-sm text-zinc-300 leading-relaxed space-y-4">
        {children}
      </div>
    </div>
  )
}

function CommandTable({ commands }: { commands: { cmd: string; desc: string }[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800 bg-zinc-900/50">
            <th className="text-left px-4 py-2.5 font-medium text-zinc-400">Command</th>
            <th className="text-left px-4 py-2.5 font-medium text-zinc-400">Description</th>
          </tr>
        </thead>
        <tbody>
          {commands.map((c, i) => (
            <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-900/30">
              <td className="px-4 py-2 font-mono text-[12px] text-green-400 whitespace-nowrap">{c.cmd}</td>
              <td className="px-4 py-2 text-zinc-400">{c.desc}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LevelTable() {
  const levels = [
    { xp: 0, level: 1, title: 'Couch Potato' },
    { xp: 50, level: 2, title: 'Reluctant Mover' },
    { xp: 150, level: 3, title: 'Warming Up' },
    { xp: 300, level: 4, title: 'Blob Warrior' },
    { xp: 500, level: 5, title: 'Sweat Apprentice' },
    { xp: 800, level: 6, title: 'Iron Blobby' },
    { xp: 1200, level: 7, title: 'Beast Mode' },
    { xp: 2500, level: 9, title: 'Mythic Monster' },
    { xp: 3500, level: 10, title: 'Transcended' },
  ]
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800 bg-zinc-900/50">
            <th className="text-left px-4 py-2.5 font-medium text-zinc-400">Level</th>
            <th className="text-left px-4 py-2.5 font-medium text-zinc-400">Title</th>
            <th className="text-right px-4 py-2.5 font-medium text-zinc-400">XP Required</th>
          </tr>
        </thead>
        <tbody>
          {levels.map((l, i) => (
            <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-900/30">
              <td className="px-4 py-2 text-cyan-400 font-medium">{l.level}</td>
              <td className="px-4 py-2 text-white">{l.title}</td>
              <td className="px-4 py-2 text-right text-amber-400 font-mono text-xs">{l.xp.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function HumanDocs() {
  return (
    <>
      <Section icon={Zap} title="Quick Start" color="green">
        <CodeBlock language="bash" code={`# Install dependencies
pip install rich pyfiglet

# Optional: AI features
pip install anthropic

# Run
python app.py`} />
        <p className="text-zinc-400">Config and state are auto-created in <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">~/.gitfit/</code> on first run.</p>
      </Section>

      <Section icon={Dumbbell} title="Your First Session" color="cyan">
        <ol className="list-decimal list-inside space-y-2 text-zinc-400">
          <li>Run <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">python app.py</code> -- the interactive menu opens</li>
          <li>Press <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">1</code> to start today's workout</li>
          <li>Blobby guides you through each exercise with animated timers</li>
          <li>After the session: XP earned, streak updated, achievements checked</li>
          <li>Run <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">python app.py profile</code> to see your GitFitHub profile</li>
        </ol>
      </Section>

      <Section icon={Terminal} title="All Commands" color="green">
        <h3 className="text-base font-semibold text-white !mt-0">Training</h3>
        <CommandTable commands={[
          { cmd: 'python app.py', desc: 'Interactive menu' },
          { cmd: 'python app.py start', desc: 'Start today\'s workout immediately' },
          { cmd: 'python app.py skip', desc: 'Skip to next workout in rotation' },
        ]} />

        <h3 className="text-base font-semibold text-white">Stats & Profile</h3>
        <CommandTable commands={[
          { cmd: 'python app.py profile', desc: 'GitFitHub profile: activity grid, muscle volume, stats' },
          { cmd: 'python app.py stats', desc: 'XP, level, streaks, progression' },
          { cmd: 'python app.py history', desc: 'Workout history table' },
          { cmd: 'python app.py achievements', desc: 'All achievements (locked + unlocked)' },
          { cmd: 'python app.py plan', desc: 'Weekly plan with suggested days' },
        ]} />

        <h3 className="text-base font-semibold text-white">Library & Forking</h3>
        <CommandTable commands={[
          { cmd: 'python app.py browse', desc: 'Interactive library browser' },
          { cmd: 'python app.py browse --list', desc: 'List all library workouts as JSON' },
          { cmd: 'python app.py fork "gitfit/slug"', desc: 'Fork a library workout' },
          { cmd: 'python app.py fork "slug" --adapt "..."', desc: 'AI-powered fork' },
        ]} />

        <h3 className="text-base font-semibold text-white">Data</h3>
        <CommandTable commands={[
          { cmd: 'python app.py log "note"', desc: 'Attach a note to the last session' },
          { cmd: 'python app.py export', desc: 'Export history as CSV' },
          { cmd: 'python app.py export --json', desc: 'Export full config + state as JSON' },
          { cmd: 'python app.py export-ow N', desc: 'Export workout N as openWorkout JSON' },
          { cmd: 'python app.py import-ow file.json', desc: 'Import an openWorkout file' },
        ]} />

        <h3 className="text-base font-semibold text-white">AI Features <span className="text-xs text-zinc-500 font-normal">(needs API key)</span></h3>
        <CommandTable commands={[
          { cmd: 'python app.py coach', desc: 'AI coaching advice' },
          { cmd: 'python app.py generate "desc"', desc: 'AI workout generation' },
          { cmd: 'python app.py adapt', desc: 'AI adapts workouts to your progress' },
          { cmd: 'python app.py setup-key', desc: 'Interactive API key setup' },
        ]} />
      </Section>

      <Section icon={GitFork} title="Forking Workouts" color="purple">
        <p className="text-zinc-400">Fork any workout from the library to your local config. Optionally let AI adapt it:</p>
        <CodeBlock language="bash" code={`# Simple fork
python app.py fork "gitfit/arnold-golden-era"

# AI-powered adaptation
python app.py fork "gitfit/arnold-golden-era" --adapt "beginner, bodyweight only, 15min max"

# Browse the library first
python app.py browse`} />
      </Section>

      <Section icon={TrendingUp} title="Leveling & XP" color="amber">
        <p className="text-zinc-400">
          <span className="text-amber-400 font-medium">XP Formula:</span>{' '}
          <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-xs text-zinc-300">10 + (duration_min * 2) + (exercises * rounds * 3)</code>
        </p>
        <LevelTable />
        <p className="text-zinc-400">Blobby evolves through 5 stages as you level up: <span className="text-yellow-400">Baby Blob</span> → <span className="text-green-400">Blob Warrior</span> → <span className="text-cyan-400">Iron Blobby</span> → <span className="text-red-400">Beast Mode</span> → <span className="text-white font-medium">Transcended</span></p>
      </Section>

      <Section icon={Trophy} title="Achievements" color="red">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {[
            { name: 'First Steps', trigger: '1 session' },
            { name: 'Getting Started', trigger: '5 sessions' },
            { name: 'Dedicated', trigger: '10 sessions' },
            { name: 'Committed', trigger: '25 sessions' },
            { name: 'Half Century', trigger: '50 sessions' },
            { name: 'Centurion', trigger: '100 sessions' },
            { name: 'On Fire', trigger: '3-day streak' },
            { name: 'Week Warrior', trigger: '7-day streak' },
            { name: 'Two Weeks Strong', trigger: '14-day streak' },
            { name: 'Monthly Monster', trigger: '30-day streak' },
            { name: 'Endurance King', trigger: '30+ min session' },
            { name: 'XP Hunter', trigger: '500 XP' },
            { name: 'XP Master', trigger: '2000 XP' },
            { name: 'Halfway There', trigger: 'Level 5' },
            { name: 'Max Level', trigger: 'Level 10' },
          ].map((a, i) => (
            <div key={i} className="flex items-center gap-3 bg-zinc-900/50 border border-zinc-800/50 rounded-lg px-3 py-2">
              <Trophy className="w-4 h-4 text-amber-400 shrink-0" />
              <div>
                <div className="text-white text-xs font-medium">{a.name}</div>
                <div className="text-zinc-500 text-[11px]">{a.trigger}</div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section icon={BookOpen} title="Configuration" color="cyan">
        <p className="text-zinc-400">Edit <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">~/.gitfit/config.json</code>:</p>
        <CodeBlock language="jsonc" code={`{
  "profile": {
    "name": "Your Name",
    "target_sessions_per_week": 3
  },
  "settings": {
    "countdown_seconds": 5,
    "rest_between_exercises": 20,
    "rest_between_rounds": 45,
    "progression_every_completed_sessions": 3,
    "progression_seconds_step": 5,
    "webhook_url": null,
    "anthropic_api_key": null
  },
  "workouts": [...]
}`} />
      </Section>
    </>
  )
}

function AgentDocs() {
  return (
    <>
      <Section icon={Zap} title="Quick Reference" color="green">
        <CodeBlock language="bash" code={`# Read current state (JSON to stdout)
python app.py status

# List library workouts (JSON to stdout)
python app.py browse --list

# Fork a workout
python app.py fork "gitfit/arnold-golden-era"

# AI-fork (adapt via Claude)
python app.py fork "gitfit/arnold-golden-era" --adapt "beginner, bodyweight, 15min"

# Export workout as openWorkout JSON
python app.py export-ow 1

# Import openWorkout JSON
python app.py import-ow workout.json

# Full state + config export (JSON)
python app.py export --json`} />
      </Section>

      <Section icon={Terminal} title="Machine-Readable Commands" color="cyan">
        <h3 className="text-base font-semibold text-white !mt-0">status → JSON</h3>
        <CodeBlock language="json" code={`{
  "completed_sessions": 12,
  "current_workout_index": 0,
  "current_workout_name": "Workout A",
  "exercise_progress": {"Push-Ups": 5, "Squats": 10},
  "xp": 340,
  "level": 4,
  "level_title": "Blob Warrior",
  "current_streak": 5,
  "longest_streak": 8,
  "last_workout_date": "2026-03-14",
  "achievements_count": "6/15",
  "history_count": 12,
  "last_session": {
    "date": "2026-03-14 08:30:00",
    "workout": "Workout C",
    "duration_min": 18.2
  }
}`} />

        <h3 className="text-base font-semibold text-white">browse --list → JSON</h3>
        <CodeBlock language="json" code={`[
  {"slug": "gitfit/arnold-golden-era", "name": "Arnold Golden Era", "rounds": 4, "exercises": 7},
  {"slug": "gitfit/quick-10min", "name": "Quick 10min", "rounds": 2, "exercises": 3}
]`} />
      </Section>

      <Section icon={BookOpen} title="openWorkout Format v1.0" color="green">
        <CodeBlock language="json" code={`{
  "openworkout_version": "1.0",
  "id": "uuid-v4",
  "name": "Workout Name",
  "description": "What this workout targets.",
  "author": {"name": "author-name"},
  "forked_from": null,
  "tags": ["bodyweight", "beginner"],
  "difficulty": "beginner | intermediate | advanced | expert",
  "estimated_duration_min": 20,
  "equipment": ["none"],
  "muscle_groups": ["chest", "quads", "core"],
  "rounds": 3,
  "exercises": [
    {
      "name": "Push-Ups",
      "mode": "time",
      "value": 30,
      "muscle_groups": ["chest", "shoulders", "triceps"]
    }
  ]
}`} />

        <h3 className="text-base font-semibold text-white">Exercises with Built-in Animations</h3>
        <p className="text-zinc-400">Prefer these names when creating workouts (they have ASCII art in the CLI):</p>
        <div className="flex flex-wrap gap-2">
          {['Push-Ups', 'Squats', 'Plank', 'Reverse Lunges', 'Superman', 'Side Plank Left', 'Side Plank Right', 'Glute Bridge', 'Bird Dog'].map(name => (
            <span key={name} className="px-2 py-1 text-xs font-mono bg-zinc-800 border border-zinc-700 rounded text-yellow-400">{name}</span>
          ))}
        </div>

        <h3 className="text-base font-semibold text-white">Muscle Group Vocabulary</h3>
        <div className="flex flex-wrap gap-2">
          {['chest', 'shoulders', 'triceps', 'quads', 'glutes', 'hamstrings', 'core', 'obliques', 'lower back'].map(name => (
            <span key={name} className="px-2 py-1 text-xs font-mono bg-zinc-800 border border-zinc-700 rounded text-green-400">{name}</span>
          ))}
        </div>

        <h3 className="text-base font-semibold text-white">Exercise Rules</h3>
        <CommandTable commands={[
          { cmd: 'mode: "time"', desc: 'value = seconds (typical range: 15-60)' },
          { cmd: 'mode: "reps"', desc: 'value = rep count (typical range: 5-25)' },
          { cmd: 'exercises', desc: '4-7 per workout is typical' },
          { cmd: 'rounds', desc: '2-4 is typical' },
        ]} />
      </Section>

      <Section icon={Terminal} title="Direct Config Modification" color="purple">
        <p className="text-zinc-400">Agents can read/write <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">~/.gitfit/config.json</code> directly.</p>

        <h3 className="text-base font-semibold text-white">Adding a Workout</h3>
        <p className="text-zinc-400">Append to the <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">workouts</code> array:</p>
        <CodeBlock language="json" code={`{
  "name": "My New Workout",
  "rounds": 3,
  "exercises": [
    {"name": "Push-Ups", "mode": "time", "value": 30},
    {"name": "Squats", "mode": "time", "value": 40}
  ],
  "_meta": {
    "forked_from": "gitfit/arnold-golden-era",
    "author": "agent-name",
    "difficulty": "beginner"
  }
}`} />

        <h3 className="text-base font-semibold text-white">Editable Settings</h3>
        <CommandTable commands={[
          { cmd: 'countdown_seconds', desc: 'Pre-exercise countdown (default: 5)' },
          { cmd: 'rest_between_exercises', desc: 'Rest seconds between exercises (default: 20)' },
          { cmd: 'rest_between_rounds', desc: 'Rest seconds between rounds (default: 45)' },
          { cmd: 'progression_every_completed_sessions', desc: 'Sessions before auto-progression (default: 3)' },
          { cmd: 'progression_seconds_step', desc: 'Seconds added per progression (default: 5)' },
          { cmd: 'webhook_url', desc: 'POST JSON here on workout completion' },
        ]} />
      </Section>

      <Section icon={Zap} title="Webhook Payload" color="amber">
        <p className="text-zinc-400">On workout completion, if <code className="text-green-400 bg-zinc-800 px-1.5 py-0.5 rounded text-xs">webhook_url</code> is set:</p>
        <CodeBlock language="json" code={`{
  "event": "workout_completed",
  "workout": "Workout A",
  "duration_min": 18.2,
  "session_number": 12,
  "xp_earned": 85,
  "level": 4,
  "level_title": "Blob Warrior",
  "streak": 5,
  "new_achievements": ["Dedicated"],
  "timestamp": "2026-03-14T08:30:00"
}`} />
      </Section>

      <Section icon={TrendingUp} title="Gamification System" color="amber">
        <p className="text-zinc-400">
          <span className="text-amber-400 font-medium">XP Formula:</span>{' '}
          <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-xs text-zinc-300">10 + (duration_min * 2) + (exercise_count * rounds * 3)</code>
        </p>
        <LevelTable />

        <h3 className="text-base font-semibold text-white">Progression</h3>
        <p className="text-zinc-400">
          Every <code className="text-zinc-300 bg-zinc-800 px-1 py-0.5 rounded text-xs">progression_every_completed_sessions</code> sessions,
          all time-based exercises gain <code className="text-zinc-300 bg-zinc-800 px-1 py-0.5 rounded text-xs">progression_seconds_step</code> seconds.
          Tracked in <code className="text-green-400 bg-zinc-800 px-1 py-0.5 rounded text-xs">state.json → exercise_progress</code>.
        </p>
      </Section>

      <Section icon={Bot} title="Agent Workflows" color="purple">
        <h3 className="text-base font-semibold text-white !mt-0">Check if user should train today</h3>
        <CodeBlock language="bash" code={`python app.py status
# Parse JSON → check last_workout_date vs today
# Check current_streak to encourage consistency`} />

        <h3 className="text-base font-semibold text-white">Create a personalized workout</h3>
        <CodeBlock language="bash" code={`# AI generation
python app.py generate "upper body, 20 minutes, intermediate"

# AI fork from library
python app.py fork "gitfit/arnold-golden-era" --adapt "beginner, no equipment"

# Or write directly to config.json`} />

        <h3 className="text-base font-semibold text-white">Analyze training patterns</h3>
        <CodeBlock language="bash" code={`python app.py export --json
# Parse full state → analyze history for patterns
# Check volume data for muscle group balance`} />
      </Section>

      <Section icon={BookOpen} title="Data Locations" color="cyan">
        <CommandTable commands={[
          { cmd: '~/.gitfit/config.json', desc: 'Workouts, settings, profile' },
          { cmd: '~/.gitfit/state.json', desc: 'History, XP, level, streak, achievements' },
          { cmd: 'workouts/gitfit--*.gitfit', desc: 'Curated workout library files' },
          { cmd: 'workouts/_template.gitfit', desc: 'openWorkout format template' },
        ]} />
      </Section>
    </>
  )
}

export function DocsPage() {
  const [tab, setTab] = useState<Tab>('humans')

  return (
    <div className="py-12 sm:py-16">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
            Documentation
          </h1>
          <p className="text-zinc-400 text-lg">
            Everything you need to get started with GitFitHub.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 mb-10 w-fit">
          <button
            onClick={() => setTab('humans')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              tab === 'humans'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-300'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            For Humans
          </button>
          <button
            onClick={() => setTab('agents')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              tab === 'agents'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-300'
            }`}
          >
            <Bot className="w-4 h-4" />
            For AI Agents
          </button>
        </div>

        {/* Content */}
        {tab === 'humans' ? <HumanDocs /> : <AgentDocs />}
      </div>
    </div>
  )
}
