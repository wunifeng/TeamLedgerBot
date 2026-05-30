import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider, useApp } from '@/context/AppContext'
import { Layout } from '@/components/Layout'
import DashboardPage from '@/pages/Dashboard/DashboardPage'
import TransactionsPage from '@/pages/Transactions/TransactionsPage'
import ExpensesPage from '@/pages/Expenses/ExpensesPage'
import MembersPage from '@/pages/Members/MembersPage'
import SettingsPage from '@/pages/Settings/SettingsPage'
import LoginPage from '@/pages/Login/LoginPage'

/** 路由守卫：未登录时跳转 /login */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { currentMember } = useApp()
  if (!currentMember) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          {/* 登录页不需要 Layout 和鉴权 */}
          <Route path="/login" element={<LoginPage />} />

          {/* 需要登录的页面 */}
          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/expenses" element={<ExpensesPage />} />
            <Route path="/members" element={<MembersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  )
}
