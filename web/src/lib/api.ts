/**
 * API client wrapper for GitFitHub backend.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getToken(): string | null {
  return localStorage.getItem('gitfit_token')
}

function setToken(token: string) {
  localStorage.setItem('gitfit_token', token)
}

function clearToken() {
  localStorage.removeItem('gitfit_token')
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || `API error ${res.status}`)
  }

  return res.json()
}

// ── Auth ──────────────────────────────────────────────────────────

export interface AuthResponse {
  user: UserProfile
  token: string
}

export interface UserProfile {
  id: number
  username: string
  email?: string
  name: string
  bio: string
  joined: string
  public_profile: boolean
  share_activity: boolean
  ai_provider: string
}

export async function login(usernameOrEmail: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
  })
  setToken(data.token)
  return data
}

export async function register(username: string, email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  })
  setToken(data.token)
  return data
}

export async function getMe(): Promise<UserProfile> {
  return apiFetch<UserProfile>('/auth/me')
}

export async function updateProfile(fields: Partial<UserProfile>): Promise<UserProfile> {
  return apiFetch<UserProfile>('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(fields),
  })
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiFetch('/auth/password', {
    method: 'PATCH',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
}

export async function deleteAccount(): Promise<void> {
  await apiFetch('/auth/me', { method: 'DELETE' })
  clearToken()
}

// ── CLI Tokens ───────────────────────────────────────────────────

export interface CLIToken {
  token_hash: string
  name: string
  created_at: string
  last_used: string | null
  token_prefix: string
}

export interface CLITokenCreated {
  token: string
  token_hash: string
}

export async function getCLITokens(): Promise<CLIToken[]> {
  return apiFetch<CLIToken[]>('/auth/cli-tokens')
}

export async function createCLIToken(name: string = 'CLI Token'): Promise<CLITokenCreated> {
  return apiFetch<CLITokenCreated>('/auth/cli-tokens', {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export async function revokeCLIToken(tokenHash: string): Promise<void> {
  await apiFetch(`/auth/cli-tokens/${tokenHash}`, { method: 'DELETE' })
}

// ── Public Profiles ──────────────────────────────────────────────

export interface PublicProfile {
  username: string
  name: string
  bio: string
  joined: string
  level: number
  level_title: string
  completed_sessions: number
  xp: number
  current_streak: number
  longest_streak: number
  public_workouts: PublicWorkout[]
}

export interface PublicWorkout {
  slug: string
  workout_json: Record<string, unknown>
  forked_from: string | null
  created_at: string
}

export interface ActivityDay {
  date: string
  count: number
}

export async function getPublicProfile(username: string): Promise<PublicProfile> {
  return apiFetch<PublicProfile>(`/users/${username}`)
}

export async function getUserActivity(username: string): Promise<ActivityDay[]> {
  return apiFetch<ActivityDay[]>(`/users/${username}/activity`)
}

// ── AI Settings ──────────────────────────────────────────────────

export async function updateAISettings(provider: string, apiKey?: string): Promise<UserProfile> {
  const body: Record<string, string> = { ai_provider: provider }
  if (apiKey !== undefined) {
    if (provider === 'openai') {
      body.openai_api_key = apiKey
    } else {
      body.anthropic_api_key = apiKey
    }
  }
  return updateProfile(body as unknown as Partial<UserProfile>)
}

// ── Token helpers ────────────────────────────────────────────────

export { getToken, setToken, clearToken }
