import axios from 'axios'

const ACCESS_KEY = 'realestate_access'
const REFRESH_KEY = 'realestate_refresh'

function getStoredAccess() {
  return localStorage.getItem(ACCESS_KEY)
}

/**
 * In dev, Vite proxies `/api` → Django (see vite.config.js).
 * In production, set VITE_API_URL (e.g. https://api.example.com) — no trailing slash.
 */
function resolveBaseURL() {
  if (import.meta.env.DEV) {
    return ''
  }
  const origin = import.meta.env.VITE_API_URL || ''
  return origin.replace(/\/$/, '')
}

export const api = axios.create({
  baseURL: resolveBaseURL(),
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = getStoredAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(ACCESS_KEY)
      localStorage.removeItem(REFRESH_KEY)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

export function setTokens(access, refresh) {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function getAccessToken() {
  return getStoredAccess()
}
