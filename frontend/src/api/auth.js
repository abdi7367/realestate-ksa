import { api, setTokens, clearTokens } from './client'

export async function login(username, password) {
  const { data } = await api.post('/api/auth/token/', { username, password })
  setTokens(data.access, data.refresh)
  return data
}

export function logout() {
  clearTokens()
}

export function decodeJwtPayload(token) {
  if (!token) return null
  try {
    const part = token.split('.')[1]
    const json = atob(part.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(
      decodeURIComponent(
        json
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join(''),
      ),
    )
  } catch {
    return null
  }
}
