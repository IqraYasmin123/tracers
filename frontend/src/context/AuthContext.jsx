import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as apiClient from '../api/client'

const AuthContext = createContext(null)

/** Wraps the framework-agnostic auth functions in api/client.js with React state. Checks
 * for a stored token on mount and validates it against /auth/me — a token could be
 * expired or the account could have been deleted since it was issued, so "a token exists
 * in localStorage" isn't the same as "the user is actually logged in". */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading') // loading | authenticated | unauthenticated

  const refreshUser = useCallback(async () => {
    const token = apiClient.getStoredToken()
    if (!token) {
      setUser(null)
      setStatus('unauthenticated')
      return
    }
    try {
      const me = await apiClient.getCurrentUser()
      setUser(me)
      setStatus('authenticated')
    } catch {
      // Stored token is invalid/expired, or the account no longer exists — same handling
      // either way: clear it and treat this as a logged-out session.
      apiClient.clearStoredToken()
      setUser(null)
      setStatus('unauthenticated')
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  async function login(usernameOrEmail, password) {
    await apiClient.login(usernameOrEmail, password)
    await refreshUser()
  }

  function logout() {
    apiClient.logout()
    setUser(null)
    setStatus('unauthenticated')
  }

  return (
    <AuthContext.Provider value={{ user, status, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
