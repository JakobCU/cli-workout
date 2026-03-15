import { useState, useEffect, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import {
  updateProfile,
  changePassword,
  deleteAccount,
  getCLITokens,
  createCLIToken,
  revokeCLIToken,
  type CLIToken,
} from '../lib/api'
import { Copy, Check, Trash2, Plus, Key } from 'lucide-react'

type Tab = 'profile' | 'tokens' | 'ai' | 'account'

export function SettingsPage() {
  const { user, isAuthenticated, loading: authLoading, refreshUser, logout } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('profile')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login')
    }
  }, [authLoading, isAuthenticated, navigate])

  if (authLoading || !user) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-zinc-400">Loading...</div>
      </div>
    )
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'profile', label: 'Profile' },
    { id: 'tokens', label: 'CLI Tokens' },
    { id: 'ai', label: 'AI Provider' },
    { id: 'account', label: 'Account' },
  ]

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-zinc-800 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.id
                ? 'text-white bg-zinc-800 border-b-2 border-green-500'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'profile' && <ProfileTab user={user} onUpdate={refreshUser} />}
      {activeTab === 'tokens' && <TokensTab />}
      {activeTab === 'ai' && <AITab user={user} onUpdate={refreshUser} />}
      {activeTab === 'account' && <AccountTab onLogout={logout} />}
    </div>
  )
}

// ── Profile Tab ──────────────────────────────────────────────────

function ProfileTab({ user, onUpdate }: { user: { name: string; bio: string; public_profile: boolean; share_activity: boolean }; onUpdate: () => Promise<void> }) {
  const [name, setName] = useState(user.name)
  const [bio, setBio] = useState(user.bio)
  const [publicProfile, setPublicProfile] = useState(user.public_profile)
  const [shareActivity, setShareActivity] = useState(user.share_activity)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await updateProfile({ name, bio, public_profile: publicProfile, share_activity: shareActivity })
      await onUpdate()
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-1">Display Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:outline-none focus:border-green-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-1">Bio</label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:outline-none focus:border-green-500 resize-none"
        />
      </div>
      <div className="space-y-3">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={publicProfile}
            onChange={(e) => setPublicProfile(e.target.checked)}
            className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-green-500 focus:ring-green-500"
          />
          <span className="text-sm text-zinc-300">Public profile</span>
        </label>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={shareActivity}
            onChange={(e) => setShareActivity(e.target.checked)}
            className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-green-500 focus:ring-green-500"
          />
          <span className="text-sm text-zinc-300">Share activity grid</span>
        </label>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <button
        type="submit"
        disabled={saving}
        className="px-6 py-2 bg-green-600 hover:bg-green-500 disabled:bg-green-800 text-white font-medium rounded-lg transition-colors"
      >
        {saving ? 'Saving...' : success ? 'Saved!' : 'Save profile'}
      </button>
    </form>
  )
}

// ── Tokens Tab ───────────────────────────────────────────────────

function TokensTab() {
  const [tokens, setTokens] = useState<CLIToken[]>([])
  const [newToken, setNewToken] = useState('')
  const [tokenName, setTokenName] = useState('')
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    getCLITokens().then(setTokens).finally(() => setLoading(false))
  }, [])

  async function handleCreate() {
    const name = tokenName.trim() || 'CLI Token'
    const result = await createCLIToken(name)
    setNewToken(result.token)
    setTokenName('')
    const updated = await getCLITokens()
    setTokens(updated)
  }

  async function handleRevoke(hash: string) {
    await revokeCLIToken(hash)
    setTokens(tokens.filter((t) => t.token_hash !== hash))
  }

  function handleCopy() {
    navigator.clipboard.writeText(newToken)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) return <div className="text-zinc-400">Loading tokens...</div>

  return (
    <div className="space-y-6">
      <p className="text-sm text-zinc-400">
        CLI tokens let you link your local CLI to your GitFitHub account.
        Use <code className="text-green-400">python app.py link &lt;token&gt;</code> to connect.
      </p>

      {/* Create new token */}
      <div className="flex gap-2">
        <input
          type="text"
          value={tokenName}
          onChange={(e) => setTokenName(e.target.value)}
          placeholder="Token name (optional)"
          className="flex-1 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-green-500"
        />
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Generate
        </button>
      </div>

      {/* Newly created token (shown once) */}
      {newToken && (
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <p className="text-sm text-green-400 font-medium mb-2">
            Token created! Copy it now -- it won't be shown again.
          </p>
          <div className="flex items-center gap-2 bg-zinc-900 rounded px-3 py-2">
            <code className="text-sm text-white flex-1 break-all">{newToken}</code>
            <button onClick={handleCopy} className="p-1 text-zinc-400 hover:text-white">
              {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
          <div className="mt-2 p-2 bg-zinc-900 rounded">
            <code className="text-xs text-zinc-400">python app.py link {newToken}</code>
          </div>
        </div>
      )}

      {/* Token list */}
      <div className="space-y-2">
        {tokens.map((t) => (
          <div key={t.token_hash} className="flex items-center justify-between p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
            <div className="flex items-center gap-3">
              <Key className="w-4 h-4 text-zinc-500" />
              <div>
                <p className="text-sm text-white">{t.name}</p>
                <p className="text-xs text-zinc-500">
                  {t.token_prefix}... | Created {new Date(t.created_at).toLocaleDateString()}
                  {t.last_used && ` | Last used ${new Date(t.last_used).toLocaleDateString()}`}
                </p>
              </div>
            </div>
            <button
              onClick={() => handleRevoke(t.token_hash)}
              className="p-2 text-zinc-500 hover:text-red-400 transition-colors"
              title="Revoke token"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        {tokens.length === 0 && (
          <p className="text-sm text-zinc-500">No CLI tokens yet.</p>
        )}
      </div>
    </div>
  )
}

// ── AI Tab ───────────────────────────────────────────────────────

function AITab({ user, onUpdate }: { user: { ai_provider: string }; onUpdate: () => Promise<void> }) {
  const [provider, setProvider] = useState(user.ai_provider || 'anthropic')
  const [apiKey, setApiKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    setSaving(true)
    setError('')
    try {
      const fields: Record<string, unknown> = { ai_provider: provider }
      if (apiKey) {
        if (provider === 'openai') {
          fields.openai_api_key = apiKey
        } else {
          fields.anthropic_api_key = apiKey
        }
      }
      await updateProfile(fields as Parameters<typeof updateProfile>[0])
      await onUpdate()
      setApiKey('')
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-3">AI Provider</label>
        <div className="space-y-2">
          {['anthropic', 'openai'].map((p) => (
            <label key={p} className="flex items-center gap-3 p-3 bg-zinc-900 border border-zinc-800 rounded-lg cursor-pointer hover:border-zinc-700">
              <input
                type="radio"
                name="provider"
                value={p}
                checked={provider === p}
                onChange={() => setProvider(p)}
                className="text-green-500 focus:ring-green-500"
              />
              <div>
                <p className="text-sm text-white font-medium capitalize">{p}</p>
                <p className="text-xs text-zinc-500">
                  {p === 'anthropic' ? 'Claude Sonnet -- recommended' : 'GPT-4o'}
                </p>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-1">
          API Key ({provider === 'anthropic' ? 'Anthropic' : 'OpenAI'})
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder={provider === 'anthropic' ? 'sk-ant-...' : 'sk-...'}
          className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-green-500"
        />
        <p className="mt-1 text-xs text-zinc-500">Leave empty to keep current key. Keys are stored encrypted.</p>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
      <button
        onClick={handleSave}
        disabled={saving}
        className="px-6 py-2 bg-green-600 hover:bg-green-500 disabled:bg-green-800 text-white font-medium rounded-lg transition-colors"
      >
        {saving ? 'Saving...' : success ? 'Saved!' : 'Save AI settings'}
      </button>
    </div>
  )
}

// ── Account Tab ──────────────────────────────────────────────────

function AccountTab({ onLogout }: { onLogout: () => void }) {
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [pwSaving, setPwSaving] = useState(false)
  const [pwSuccess, setPwSuccess] = useState(false)
  const [pwError, setPwError] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault()
    if (newPassword.length < 8) {
      setPwError('Password must be at least 8 characters')
      return
    }
    setPwSaving(true)
    setPwError('')
    try {
      await changePassword(currentPassword, newPassword)
      setPwSuccess(true)
      setCurrentPassword('')
      setNewPassword('')
      setTimeout(() => setPwSuccess(false), 2000)
    } catch (err) {
      setPwError(err instanceof Error ? err.message : 'Failed to change password')
    } finally {
      setPwSaving(false)
    }
  }

  async function handleDelete() {
    try {
      await deleteAccount()
      onLogout()
      navigate('/')
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-8">
      {/* Change Password */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Change Password</h3>
        <form onSubmit={handleChangePassword} className="space-y-4 max-w-sm">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">Current password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:outline-none focus:border-green-500"
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">New password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:outline-none focus:border-green-500"
              autoComplete="new-password"
            />
          </div>
          {pwError && <p className="text-red-400 text-sm">{pwError}</p>}
          <button
            type="submit"
            disabled={pwSaving}
            className="px-6 py-2 bg-green-600 hover:bg-green-500 disabled:bg-green-800 text-white font-medium rounded-lg transition-colors"
          >
            {pwSaving ? 'Updating...' : pwSuccess ? 'Updated!' : 'Update password'}
          </button>
        </form>
      </div>

      {/* Danger Zone */}
      <div className="border border-red-500/20 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-red-400 mb-2">Danger Zone</h3>
        <p className="text-sm text-zinc-400 mb-4">
          Once you delete your account, there is no going back.
        </p>
        {!deleteConfirm ? (
          <button
            onClick={() => setDeleteConfirm(true)}
            className="px-4 py-2 border border-red-500/30 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors text-sm"
          >
            Delete account
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-sm text-red-400">Are you sure?</span>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors text-sm"
            >
              Yes, delete my account
            </button>
            <button
              onClick={() => setDeleteConfirm(false)}
              className="px-4 py-2 text-zinc-400 hover:text-white text-sm"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
