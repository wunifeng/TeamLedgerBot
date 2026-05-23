import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
  maxWidth?: number
}

export function Modal({ isOpen, onClose, title, children, maxWidth = 480 }: ModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(4px)',
              zIndex: 1000,
            }}
          />

          {/* Dialog */}
          <motion.div
            key="dialog"
            initial={{ opacity: 0, scale: 0.94, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 16 }}
            transition={{ type: 'spring', stiffness: 380, damping: 28 }}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1001,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '16px',
              pointerEvents: 'none',
            }}
          >
            <div
              className="glass-card"
              style={{
                width: '100%',
                maxWidth,
                maxHeight: '90dvh',
                overflowY: 'auto',
                pointerEvents: 'auto',
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '20px 24px 16px',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {title}
                </h2>
                <button
                  onClick={onClose}
                  className="btn btn-ghost btn-icon btn-sm"
                  style={{ marginRight: -4 }}
                >
                  <X size={16} />
                </button>
              </div>

              {/* Body */}
              <div style={{ padding: '20px 24px 24px' }}>{children}</div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
