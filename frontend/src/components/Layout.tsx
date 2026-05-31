import { Outlet } from 'react-router-dom'
import { Sidebar } from './Navigation/Sidebar'
import { BottomNav } from './Navigation/BottomNav'

export function Layout() {
  return (
    <div className="layout-root">
      <Sidebar />
      <main className="layout-main">
        <div className="layout-content">
          <Outlet />
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
