/**
 * AuthContext + AuthProvider for GitFitHub web auth.
 */

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { type UserProfile, getMe, login as apiLogin, register as apiRegister, clearToken, getToken } from './api'

interface AuthContextType {
  user: UserProfile | null
  loading: boolean
  isAuthenticated: boolean
  login: (usernameOrEmail: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const me = await getMe()
      setUser(me)
    } catch {
      setUser(null)
      clearToken()
    }
  }, [])

  useEffect(() => {
    const token = getToken()
    if (token) {
      refreshUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [refreshUser])

  const login = async (usernameOrEmail: string, password: string) => {
    const res = await apiLogin(usernameOrEmail, password)
    setUser(res.user)
  }

  const register = async (username: string, email: string, password: string) => {
    const res = await apiRegister(username, email, password)
    setUser(res.user)
  }

  const logout = () => {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
