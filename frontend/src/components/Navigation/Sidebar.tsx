import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ArrowLeftRight, ReceiptText, Users, Settings } from 'lucide-react'
import { motion } from 'framer-motion'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘', end: true },
  { to: '/transactions', icon: ArrowLeftRight, label: '流水明细' },
  { to: '/expenses', icon: ReceiptText, label: '成员垫付' },
  { to: '/members', icon: Users, label: '成员管理' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export function Sidebar() {
  return (
    <aside
      className="layout-sidebar glass-card"
      style={{
        borderRadius: 0,
        borderTop: 'none',
        borderBottom: 'none',
        borderLeft: 'none',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        background: 'rgba(9, 16, 31, 0.85)',
      }}
    >
      {/* Logo */}
      <div style={{ padding: '0 20px 28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, var(--brand-primary), var(--brand-dark))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-glow-indigo)',
              fontSize: 18,
            }}
          >
            💰
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              TeamLedger
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>财务管理平台</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '0 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            style={{ textDecoration: 'none' }}
          >
            {({ isActive }) => (
              <motion.div
                whileHover={{ x: 3 }}
                whileTap={{ scale: 0.97 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 12px',
                  borderRadius: 10,
                  cursor: 'pointer',
                  background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.25)' : '1px solid transparent',
                  color: isActive ? 'var(--brand-light)' : 'var(--text-secondary)',
                  transition: 'all 0.15s',
                }}
              >
                <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
                <span style={{ fontSize: 14, fontWeight: isActive ? 600 : 400 }}>{label}</span>
                {isActive && (
                  <div
                    style={{
                      marginLeft: 'auto',
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: 'var(--brand-primary)',
                      boxShadow: '0 0 6px var(--brand-primary)',
                    }}
                  />
                )}
              </motion.div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div
        style={{
          padding: '16px 20px 0',
          borderTop: '1px solid var(--border-subtle)',
          marginTop: 8,
        }}
      >
        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
          TeamLedgerBot
          <br />
          <span style={{ opacity: 0.6 }}>© {new Date().getFullYear()}</span>
        </div>
      </div>
    </aside>
  )
}
