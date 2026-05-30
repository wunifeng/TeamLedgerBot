import React, { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { MemberResponse } from '@/types/api'

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
  // 认证状态
  currentMember: MemberResponse | null
  login: (member: MemberResponse, token: string) => void
  logout: () => void
}

const AppContext = createContext<AppContextValue | null>(null)

let toastIdCounter = 0

export function AppProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const [currentMember, setCurrentMember] = useState<MemberResponse | null>(null)

  // 初始化时从 localStorage 恢复登录态
  useEffect(() => {
    const savedMember = localStorage.getItem('auth_member')
    const savedToken = localStorage.getItem('auth_token')
    if (savedMember && savedToken) {
      try {
        setCurrentMember(JSON.parse(savedMember))
      } catch {
        localStorage.removeItem('auth_member')
        localStorage.removeItem('auth_token')
      }
    }
  }, [])

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

  const login = useCallback((member: MemberResponse, token: string) => {
    localStorage.setItem('auth_token', token)
    localStorage.setItem('auth_member', JSON.stringify(member))
    setCurrentMember(member)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_member')
    setCurrentMember(null)
    window.location.href = '/login'
  }, [])

  return (
    <AppContext.Provider value={{ toasts, showToast, removeToast, currentMember, login, logout }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
