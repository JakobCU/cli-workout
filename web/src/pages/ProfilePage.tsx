import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getPublicProfile, getUserActivity, type PublicProfile, type ActivityDay } from '../lib/api'
import { ActivityGrid } from '../components/ActivityGrid'
import { useAuth } from '../lib/auth'
import { Calendar, Flame, Trophy, Zap, GitFork, Settings } from 'lucide-react'

const LEVEL_COLORS: Record<string, string> = {
  'Couch Potato': 'text-zinc-400',
  'Rookie': 'text-green-400',
  'Regular': 'text-blue-400',
  'Dedicated': 'text-purple-400',
  'Warrior': 'text-orange-400',
  'Elite': 'text-yellow-400',
  'Champion': 'text-red-400',
  'Legend': 'text-pink-400',
  'Mythic': 'text-cyan-400',
  'Transcended': 'text-amber-300',
}

export function ProfilePage() {
  const { username } = useParams<{ username: string }>()
  const { user: currentUser } = useAuth()
  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [activity, setActivity] = useState<ActivityDay[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const isOwnProfile = currentUser?.username === username

  useEffect(() => {
    if (!username) return
    setLoading(true)
    Promise.all([
      getPublicProfile(username),
      getUserActivity(username),
    ])
      .then(([p, a]) => {
        setProfile(p)
        setActivity(a)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Profile not found'))
      .finally(() => setLoading(false))
  }, [username])

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-zinc-400">Loading profile...</div>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-2">User not found</h2>
          <p className="text-zinc-400">{error || 'This profile does not exist.'}</p>
        </div>
      </div>
    )
  }

  const activityMap: Record<string, number> = {}
  activity.forEach((d) => { activityMap[d.date] = d.count })

  const levelColor = LEVEL_COLORS[profile.level_title] || 'text-zinc-400'
  const initial = (profile.name || profile.username || '?')[0].toUpperCase()

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-8">
        {/* Left sidebar */}
        <aside>
          {/* Avatar */}
          <div className="w-32 h-32 rounded-full bg-zinc-800 border-2 border-zinc-700 flex items-center justify-center mx-auto lg:mx-0 mb-4">
            <span className="text-4xl font-bold text-green-400">{initial}</span>
          </div>

          <h1 className="text-xl font-bold text-white">{profile.name}</h1>
          <p className="text-zinc-400 text-sm">@{profile.username}</p>

          {profile.bio && (
            <p className="text-zinc-300 text-sm mt-3">{profile.bio}</p>
          )}

          {/* Level badge */}
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700">
            <Trophy className="w-3.5 h-3.5 text-yellow-400" />
            <span className={`text-sm font-medium ${levelColor}`}>
              Lv.{profile.level} {profile.level_title}
            </span>
          </div>

          {/* Stats */}
          <div className="mt-6 space-y-2 text-sm">
            <div className="flex items-center gap-2 text-zinc-400">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span>{profile.xp.toLocaleString()} XP</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Calendar className="w-4 h-4 text-cyan-400" />
              <span>{profile.completed_sessions} sessions</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Flame className="w-4 h-4 text-red-400" />
              <span>{profile.current_streak}d streak (best: {profile.longest_streak}d)</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Calendar className="w-4 h-4 text-zinc-500" />
              <span>Joined {profile.joined}</span>
            </div>
          </div>

          {isOwnProfile && (
            <Link
              to="/settings"
              className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2 border border-zinc-700 hover:border-zinc-600 text-zinc-300 hover:text-white rounded-lg transition-colors text-sm"
            >
              <Settings className="w-4 h-4" />
              Edit Profile
            </Link>
          )}
        </aside>

        {/* Main content */}
        <div className="space-y-8">
          {/* Activity grid */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6">
            <ActivityGrid data={activityMap} />
          </div>

          {/* Public workouts */}
          {profile.public_workouts.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Public Workouts ({profile.public_workouts.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {profile.public_workouts.map((w) => {
                  const workout = w.workout_json as Record<string, unknown>
                  return (
                    <div
                      key={w.slug}
                      className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <h3 className="font-medium text-white">
                          {(workout.name as string) || w.slug}
                        </h3>
                        {w.forked_from && (
                          <span className="inline-flex items-center gap-1 text-xs text-zinc-500">
                            <GitFork className="w-3 h-3" />
                            {w.forked_from}
                          </span>
                        )}
                      </div>
                      <div className="mt-2 text-xs text-zinc-500">
                        {(workout.rounds as number) || 3} rounds,{' '}
                        {(workout.exercises as unknown[])?.length || 0} exercises
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
