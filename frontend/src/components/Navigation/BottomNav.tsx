import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Users, Settings, ArrowLeftRight, ReceiptText } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { AddFlowReportModal } from '@/components/Forms/AddFlowReportModal'
import { AddExpenseModal } from '@/components/Forms/AddExpenseModal'
import { useApp } from '@/context/AppContext'

const sideNavItems = [
  { to: '/', icon: LayoutDashboard, label: '看板', end: true },
  { to: '/members', icon: Users, label: '成员' },
]

const sideNavItemsRight = [
  { to: '/transactions', icon: ArrowLeftRight, label: '流水' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export function BottomNav() {
  const { showToast } = useApp()
  const [showActions, setShowActions] = useState(false)
  const [flowModal, setFlowModal] = useState(false)
  const [expenseModal, setExpenseModal] = useState(false)

  const openFlow = () => {
    setShowActions(false)
    setFlowModal(true)
  }

  const openExpense = () => {
    setShowActions(false)
    setExpenseModal(true)
  }

  return (
    <>
      {/* 背景遮罩 */}
      <AnimatePresence>
        {showActions && (
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={() => setShowActions(false)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.55)',
              backdropFilter: 'blur(4px)',
              WebkitBackdropFilter: 'blur(4px)',
              zIndex: 38,
            }}
          />
        )}
      </AnimatePresence>

      {/* 上报操作弹出菜单 */}
      <AnimatePresence>
        {showActions && (
          <motion.div
            key="actions"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            style={{
              position: 'fixed',
              bottom: 'calc(var(--bottom-nav-height) + 12px)',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 50,
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              alignItems: 'center',
              width: 'min(320px, calc(100vw - 32px))',
            }}
          >
            {/* 上报流水卡片 */}
            <motion.button
              whileTap={{ scale: 0.96 }}
              onClick={openFlow}
              style={{
                width: '100%',
                padding: '16px 20px',
                borderRadius: 16,
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(79, 70, 229, 0.15))',
                border: '1px solid rgba(99, 102, 241, 0.4)',
                color: 'var(--brand-light)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                boxShadow: '0 8px 32px rgba(99, 102, 241, 0.25)',
              }}
            >
              <div style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: 'linear-gradient(135deg, var(--brand-primary), var(--brand-dark))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: 'var(--shadow-glow-indigo)',
              }}>
                <ArrowLeftRight size={20} color="#fff" strokeWidth={2} />
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.01em' }}>上报流水</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>记录每日游戏流水数据</div>
              </div>
            </motion.button>

            {/* 上报支出卡片 */}
            <motion.button
              whileTap={{ scale: 0.96 }}
              onClick={openExpense}
              style={{
                width: '100%',
                padding: '16px 20px',
                borderRadius: 16,
                background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.2), rgba(244, 63, 94, 0.1))',
                border: '1px solid rgba(244, 63, 94, 0.35)',
                color: 'var(--color-expense)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                boxShadow: '0 8px 32px rgba(244, 63, 94, 0.2)',
              }}
            >
              <div style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #f43f5e, #e11d48)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: 'var(--shadow-glow-red)',
              }}>
                <ReceiptText size={20} color="#fff" strokeWidth={2} />
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.01em' }}>上报支出</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>登记成员垫付支出</div>
              </div>
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 底部导航栏 */}
      <nav
        className="bottom-nav"
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 'var(--bottom-nav-height)',
          background: 'rgba(9, 16, 31, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderTop: '1px solid var(--border-default)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-around',
          padding: '0 4px',
          zIndex: 40,
        }}
      >
        {/* 左侧导航 */}
        {sideNavItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink key={to} to={to} end={end} style={{ textDecoration: 'none', flex: 1 }}>
            {({ isActive }) => (
              <motion.div
                whileTap={{ scale: 0.88 }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 3,
                  padding: '6px 4px',
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
                        bottom: -5,
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

        {/* 中央 FAB 上报按钮 */}
        <div style={{ flex: 1.4, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <motion.button
            whileTap={{ scale: 0.9 }}
            animate={showActions ? { rotate: 45 } : { rotate: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setShowActions((v) => !v)}
            style={{
              width: 52,
              height: 52,
              borderRadius: 16,
              background: showActions
                ? 'rgba(99, 102, 241, 0.3)'
                : 'linear-gradient(135deg, var(--brand-primary), var(--brand-dark))',
              border: showActions
                ? '1.5px solid rgba(99, 102, 241, 0.6)'
                : '1.5px solid rgba(99, 102, 241, 0.3)',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: showActions
                ? '0 0 24px rgba(99, 102, 241, 0.4)'
                : '0 4px 20px rgba(99, 102, 241, 0.45)',
              fontSize: 26,
              fontWeight: 300,
              lineHeight: 1,
              marginBottom: 4,
            }}
            aria-label="上报操作"
          >
            +
          </motion.button>
        </div>

        {/* 右侧导航 */}
        {sideNavItemsRight.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} style={{ textDecoration: 'none', flex: 1 }}>
            {({ isActive }) => (
              <motion.div
                whileTap={{ scale: 0.88 }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 3,
                  padding: '6px 4px',
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
                        bottom: -5,
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

      {/* Modals */}
      <AddFlowReportModal
        isOpen={flowModal}
        onClose={() => setFlowModal(false)}
        onSuccess={(flow) => {
          setFlowModal(false)
          showToast(`流水已上报：${flow.member_name ?? ''}`, 'success')
        }}
      />
      <AddExpenseModal
        isOpen={expenseModal}
        onClose={() => setExpenseModal(false)}
        onSuccess={() => {
          setExpenseModal(false)
          showToast('支出已登记', 'success')
        }}
      />
    </>
  )
}
