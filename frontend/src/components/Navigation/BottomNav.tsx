import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ArrowLeftRight, Users, Settings } from 'lucide-react'
import { motion } from 'framer-motion'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘', end: true },
  { to: '/transactions', icon: ArrowLeftRight, label: '流水' },
  { to: '/members', icon: Users, label: '成员' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export function BottomNav() {
  return (
    <nav
      className="bottom-nav"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: 'var(--bottom-nav-height)',
        background: 'rgba(9, 16, 31, 0.92)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        padding: '0 8px',
        zIndex: 40,
      }}
    >
      {navItems.map(({ to, icon: Icon, label, end }) => (
        <NavLink key={to} to={to} end={end} style={{ textDecoration: 'none', flex: 1 }}>
          {({ isActive }) => (
            <motion.div
              whileTap={{ scale: 0.88 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
                padding: '8px 4px',
                borderRadius: 10,
                color: isActive ? 'var(--brand-light)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              <div style={{ position: 'relative' }}>
                <Icon size={22} strokeWidth={isActive ? 2.2 : 1.6} />
                {isActive && (
                  <motion.div
                    layoutId="bottom-nav-dot"
                    style={{
                      position: 'absolute',
                      bottom: -6,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 4,
                      height: 4,
                      borderRadius: '50%',
                      background: 'var(--brand-primary)',
                      boxShadow: '0 0 8px var(--brand-primary)',
                    }}
                  />
                )}
              </div>
              <span style={{ fontSize: 10, fontWeight: isActive ? 600 : 400 }}>{label}</span>
            </motion.div>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
