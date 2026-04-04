import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'realestate-ui-theme'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [mode, setModeState] = useState(() => {
    try {
      const s = localStorage.getItem(STORAGE_KEY)
      if (s === 'dark' || s === 'light') return s
    } catch {
      /* ignore */
    }
    return 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
    document.documentElement.style.colorScheme = mode === 'dark' ? 'dark' : 'light'
    try {
      localStorage.setItem(STORAGE_KEY, mode)
    } catch {
      /* ignore */
    }
  }, [mode])

  const setMode = (next) => {
    setModeState(next === 'dark' ? 'dark' : 'light')
  }

  const toggleMode = () => setModeState((m) => (m === 'dark' ? 'light' : 'dark'))

  const value = useMemo(
    () => ({ mode, setMode, toggleMode }),
    [mode],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return ctx
}
