import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { UserPlus, Users, Wallet, BadgeCheck } from 'lucide-react'
import { format } from 'date-fns'
import { membersApi, transactionsApi } from '@/services/api'
import type { MemberResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'
import { Modal } from '@/components/UI/Modal'
import { AddTransactionModal } from '@/components/Forms/AddTransactionModal'

function MemberCard({ member, onSettle, delay }: { member: MemberResponse; onSettle: (m: MemberResponse) => void; delay: number }) {
  const initials = member.name.slice(0, 2).toUpperCase()
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#f43f5e', '#06b6d4']
  const color = colors[member.name.charCodeAt(0) % colors.length]

  return (
    <motion.div
      className="glass-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -3 }}
      style={{ padding: '20px', cursor: 'default' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 14,
          background: `${color}25`,
          border: `2px solid ${color}50`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 15, fontWeight: 700, color,
          flexShrink: 0,
        }}>
          {initials}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{member.name}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {member.role ?? '团队成员'} · 加入于 {format(new Date(member.created_at), 'yyyy-MM')}
          </div>
        </div>
        {member.is_active && (
          <BadgeCheck size={16} style={{ marginLeft: 'auto', color: 'var(--color-income)', flexShrink: 0 }} />
        )}
      </div>

      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '10px 14px',
          background: 'rgba(139,92,246,0.08)',
          borderRadius: 10,
          border: '1px solid rgba(139,92,246,0.18)',
          marginBottom: 14,
        }}
      >
        <Wallet size={14} style={{ color: 'var(--color-salary)' }} />
        <span style={{ fontSize: 13, color: 'var(--text-secondary)', flex: 1 }}>发起薪资结算</span>
        <button
          className="btn btn-sm"
          style={{
            background: 'rgba(139,92,246,0.2)', color: 'var(--color-salary)',
            border: '1px solid rgba(139,92,246,0.3)', padding: '4px 12px',
          }}
          onClick={() => onSettle(member)}
        >
          结算
        </button>
      </div>
    </motion.div>
  )
}

export default function MembersPage() {
  const { showToast } = useApp()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [addMemberOpen, setAddMemberOpen] = useState(false)
  const [settleTarget, setSettleTarget] = useState<MemberResponse | null>(null)
  const [salaryModalOpen, setSalaryModalOpen] = useState(false)

  // Add member form
  const [newName, setNewName] = useState('')
  const [newRole, setNewRole] = useState('')
  const [adding, setAdding] = useState(false)

  const loadMembers = useCallback(async () => {
    setLoading(true)
    try {
      setMembers(await membersApi.list())
    } catch (e: any) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => { loadMembers() }, [loadMembers])

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setAdding(true)
    try {
      await membersApi.create({ name: newName.trim(), role: newRole.trim() || undefined })
      showToast(`成员 ${newName} 已添加`, 'success')
      setNewName(''); setNewRole(''); setAddMemberOpen(false)
      loadMembers()
    } catch (err: any) {
      showToast(err.message, 'error')
    } finally {
      setAdding(false)
    }
  }

  const handleSettle = (member: MemberResponse) => {
    setSettleTarget(member)
    setSalaryModalOpen(true)
  }

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <h1 className="page-title">成员与薪资</h1>
            <p className="page-subtitle">管理团队成员，发起薪资结算</p>
          </div>
          <button className="btn btn-primary" onClick={() => setAddMemberOpen(true)}>
            <UserPlus size={16} />新增成员
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 160, borderRadius: 16 }} />)}
        </div>
      ) : !members.length ? (
        <div className="empty-state glass-card" style={{ padding: 64 }}>
          <Users size={48} />
          <p>暂无团队成员，点击右上角添加</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {members.map((m, i) => (
            <MemberCard key={m.id} member={m} onSettle={handleSettle} delay={i * 0.06} />
          ))}
        </div>
      )}

      {/* Add member modal */}
      <Modal isOpen={addMemberOpen} onClose={() => setAddMemberOpen(false)} title="新增团队成员">
        <form onSubmit={handleAddMember}>
          <div className="form-group">
            <label className="form-label">姓名 *</label>
            <input
              className="form-input"
              type="text"
              placeholder="例：张三"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">角色（可选）</label>
            <input
              className="form-input"
              type="text"
              placeholder="例：开发、设计、运营"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setAddMemberOpen(false)}>取消</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={adding}>
              {adding ? '添加中...' : '确认添加'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Salary settle modal - reuse AddTransactionModal pre-filled */}
      {settleTarget && (
        <AddTransactionModal
          isOpen={salaryModalOpen}
          onClose={() => { setSalaryModalOpen(false); setSettleTarget(null) }}
          onSuccess={() => {
            setSalaryModalOpen(false)
            setSettleTarget(null)
            showToast(`已为 ${settleTarget.name} 发起薪资结算`, 'success')
          }}
        />
      )}
    </>
  )
}
