import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { decodeJwtPayload, login as apiLogin, logout as apiLogout } from '../api/auth'
import { getAccessToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [tokenVersion, setTokenVersion] = useState(0)

  const token = getAccessToken()
  const payload = useMemo(() => decodeJwtPayload(token), [token, tokenVersion])

  const user = useMemo(() => {
    if (!payload) return null
    return {
      username: payload.username,
      role: payload.role,
      email: payload.email,
      nationalId: payload.national_id || '',
    }
  }, [payload])

  const isAuthenticated = Boolean(token)

  const login = useCallback(async (username, password) => {
    await apiLogin(username, password)
    setTokenVersion((v) => v + 1)
  }, [])

  const logout = useCallback(() => {
    apiLogout()
    setTokenVersion((v) => v + 1)
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthenticated,
      login,
      logout,
    }),
    [user, isAuthenticated, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
