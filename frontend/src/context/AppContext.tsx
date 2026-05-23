import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

// ── Toast ─────────────────────────────────────────────────────────────────────
export type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: number
  message: string
  type: ToastType
}

// ── Context shape ─────────────────────────────────────────────────────────────
interface AppContextValue {
  toasts: Toast[]
  showToast: (message: string, type?: ToastType) => void
  removeToast: (id: number) => void
}

const AppContext = createContext<AppContextValue | null>(null)

let toastIdCounter = 0

export function AppProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++toastIdCounter
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <AppContext.Provider value={{ toasts, showToast, removeToast }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
