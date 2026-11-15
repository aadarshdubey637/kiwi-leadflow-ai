import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { authApi } from '@/api/authApi'
import type { Admin } from '@/types/api'
import { AUTH_EXPIRED_EVENT, tokenStore } from './tokenStore'

type Status = 'loading' | 'authenticated' | 'anonymous'

interface AuthValue {
  admin: Admin | null
  status: Status
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [admin, setAdmin] = useState<Admin | null>(null)
  const [status, setStatus] = useState<Status>(tokenStore.get() ? 'loading' : 'anonymous')

  // On page load, verify a stored token with the backend (the backend — not this check — is the authority).
  useEffect(() => {
    if (!tokenStore.get()) return
    authApi
      .me()
      .then((a) => { setAdmin(a); setStatus('authenticated') })
      .catch(() => { tokenStore.clear(); setStatus('anonymous') })
  }, [])

  // axios interceptor fires this when any protected request comes back 401 (expired / invalid token).
  useEffect(() => {
    const onExpired = () => {
      setAdmin(null)
      setStatus('anonymous')
      queryClient.clear()
      toast.error('Your session has expired. Please sign in again.')
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
  }, [queryClient])

  const login = useCallback(async (username: string, password: string) => {
    const token = await authApi.login({ username, password })
    tokenStore.set(token.access_token)
    try {
      setAdmin(await authApi.me())
      setStatus('authenticated')
    } catch (e) {
      tokenStore.clear()
      throw e
    }
  }, [])

  const logout = useCallback(() => {
    // The backend uses stateless JWTs and has no logout endpoint, so logging out means discarding the token
    // and every cached query (so the next user never sees the previous admin's data).
    tokenStore.clear()
    setAdmin(null)
    setStatus('anonymous')
    queryClient.clear()
  }, [queryClient])

  const value = useMemo(() => ({ admin, status, login, logout }), [admin, status, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
