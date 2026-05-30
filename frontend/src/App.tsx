import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider } from '@/context/AppContext'
import { Layout } from '@/components/Layout'
import DashboardPage from '@/pages/Dashboard/DashboardPage'
import TransactionsPage from '@/pages/Transactions/TransactionsPage'
import ExpensesPage from '@/pages/Expenses/ExpensesPage'
import MembersPage from '@/pages/Members/MembersPage'
import SettingsPage from '@/pages/Settings/SettingsPage'

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
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
