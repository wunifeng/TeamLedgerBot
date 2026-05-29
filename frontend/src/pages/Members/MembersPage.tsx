import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  UserPlus, Users, Wallet, BadgeCheck, MoreHorizontal,
  CalendarDays, Pencil, CreditCard, ReceiptText,
} from 'lucide-react'
import { format } from 'date-fns'
import { membersApi, salaryApi } from '@/services/api'
import type { MemberResponse, SalarySettlementListResponse, SalarySettlementResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'
import { Modal } from '@/components/UI/Modal'

const emptySettlements: SalarySettlementListResponse = {
  items: [],
  total_payable: 0,
  total_paid: 0,
  total_unpaid: 0,
}

function currentMonthValue() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function periodRange(monthValue: string) {
  const [year, month] = monthValue.split('-').map(Number)
  const lastDay = new Date(year, month, 0).getDate()
  return {
    period_start: `${monthValue}-01`,
    period_end: `${monthValue}-${String(lastDay).padStart(2, '0')}`,
    label: `${year}年${month}月`,
  }
}

function money(value: number) {
  return `¥${new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value || 0)}`
}

function statusMeta(status?: SalarySettlementResponse['status']) {
  if (status === 'paid') return { label: '已结清', color: 'var(--color-income)' }
  if (status === 'partial') return { label: '部分已付', color: 'var(--color-warning)' }
  return { label: '待发放', color: 'var(--color-expense)' }
}

interface MemberCardProps {
  member: MemberResponse
  settlement?: SalarySettlementResponse
  onSetPayable: (member: MemberResponse) => void
  onPay: (member: MemberResponse, settlement: SalarySettlementResponse) => void
  onEdit: (member: MemberResponse) => void
  delay: number
}

function MemberCard({ member, settlement, onSetPayable, onPay, onEdit, delay }: MemberCardProps) {
  const initials = member.name.slice(0, 2).toUpperCase()
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#f43f5e', '#06b6d4']
  const color = colors[member.name.charCodeAt(0) % colors.length]
  const payable = settlement?.payable_amount ?? 0
  const paid = settlement?.paid_amount ?? 0
  const unpaid = settlement?.unpaid_amount ?? 0
  const percent = payable > 0 ? Math.min(100, Math.round((paid / payable) * 100)) : 0
  const status = statusMeta(settlement?.status)

  return (
    <motion.div
      className="glass-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -3 }}
      style={{ padding: '20px', cursor: 'default' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16, position: 'relative' }}>
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
        {member.is_active ? (
          <BadgeCheck size={16} style={{ marginLeft: 'auto', color: 'var(--color-income)', flexShrink: 0 }} />
        ) : (
          <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--color-expense)', backgroundColor: 'var(--color-expense)20', padding: '2px 6px', borderRadius: 6, flexShrink: 0 }}>已退出</span>
        )}

        <button
          onClick={() => onEdit(member)}
          className="btn btn-ghost btn-sm"
          style={{ position: 'absolute', top: -14, right: -14, padding: 4, color: 'var(--text-muted)' }}
          title="编辑成员"
        >
          <MoreHorizontal size={18} />
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 14 }}>
        <div style={{ padding: '10px', borderRadius: 10, background: 'rgba(255,255,255,0.035)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>应付</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{money(payable)}</div>
        </div>
        <div style={{ padding: '10px', borderRadius: 10, background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.12)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>已付</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-income)', fontVariantNumeric: 'tabular-nums' }}>{money(paid)}</div>
        </div>
        <div style={{ padding: '10px', borderRadius: 10, background: 'rgba(244,63,94,0.06)', border: '1px solid rgba(244,63,94,0.12)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>未付</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: unpaid > 0 ? 'var(--color-expense)' : 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>{money(unpaid)}</div>
        </div>
      </div>

      <div style={{ height: 7, borderRadius: 999, background: 'rgba(255,255,255,0.06)', overflow: 'hidden', marginBottom: 12 }}>
        <div style={{ height: '100%', width: `${percent}%`, background: status.color, transition: 'width 0.2s ease' }} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <span style={{ fontSize: 12, color: status.color, background: `${status.color}18`, border: `1px solid ${status.color}30`, padding: '2px 8px', borderRadius: 999 }}>
          {settlement ? status.label : '未设置'}
        </span>
        {settlement?.remark && (
          <span className="truncate-1" style={{ fontSize: 12, color: 'var(--text-muted)' }}>{settlement.remark}</span>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button
          className="btn btn-ghost btn-sm"
          style={{ flex: 1 }}
          onClick={() => onSetPayable(member)}
        >
          <Pencil size={13} />设置应付
        </button>
        <button
          className="btn btn-sm"
          style={{
            flex: 1,
            background: 'rgba(139,92,246,0.2)',
            color: 'var(--color-salary)',
            border: '1px solid rgba(139,92,246,0.3)',
          }}
          disabled={!settlement || unpaid <= 0}
          onClick={() => settlement && onPay(member, settlement)}
        >
          <CreditCard size={13} />发放
        </button>
      </div>
    </motion.div>
  )
}

export default function MembersPage() {
  const { showToast } = useApp()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [settlements, setSettlements] = useState<SalarySettlementListResponse>(emptySettlements)
  const [loading, setLoading] = useState(true)
  const [periodMonth, setPeriodMonth] = useState(currentMonthValue())
  const [addMemberOpen, setAddMemberOpen] = useState(false)

  const [newName, setNewName] = useState('')
  const [newRole, setNewRole] = useState('')
  const [adding, setAdding] = useState(false)

  const [editMemberTarget, setEditMemberTarget] = useState<MemberResponse | null>(null)
  const [editName, setEditName] = useState('')
  const [editRole, setEditRole] = useState('')
  const [editIsActive, setEditIsActive] = useState(true)
  const [editing, setEditing] = useState(false)

  const [payableTarget, setPayableTarget] = useState<MemberResponse | null>(null)
  const [payableAmount, setPayableAmount] = useState('')
  const [payableRemark, setPayableRemark] = useState('')
  const [savingPayable, setSavingPayable] = useState(false)

  const [paymentTarget, setPaymentTarget] = useState<{ member: MemberResponse; settlement: SalarySettlementResponse } | null>(null)
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentBonus, setPaymentBonus] = useState('')
  const [paymentRemark, setPaymentRemark] = useState('')
  const [paying, setPaying] = useState(false)

  const range = periodRange(periodMonth)

  const loadMembers = useCallback(async () => {
    setLoading(true)
    const nextRange = periodRange(periodMonth)
    try {
      const [memberRows, settlementRows] = await Promise.all([
        membersApi.list(true),
        salaryApi.listSettlements({
          period_start: nextRange.period_start,
          period_end: nextRange.period_end,
          include_inactive: true,
        }),
      ])
      setMembers(memberRows)
      setSettlements(settlementRows)
    } catch (e: any) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [periodMonth, showToast])

  useEffect(() => { loadMembers() }, [loadMembers])

  const getSettlement = (memberId: string) =>
    settlements.items.find((item) => item.member_id === memberId)

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setAdding(true)
    try {
      await membersApi.create({ name: newName.trim(), role: newRole.trim() || undefined })
      showToast(`成员 ${newName} 已添加`, 'success')
      setNewName('')
      setNewRole('')
      setAddMemberOpen(false)
      loadMembers()
    } catch (err: any) {
      showToast(err.message, 'error')
    } finally {
      setAdding(false)
    }
  }

  const handlePayableOpen = (member: MemberResponse) => {
    const settlement = getSettlement(member.id)
    setPayableTarget(member)
    setPayableAmount(settlement ? String(settlement.payable_amount) : '')
    setPayableRemark(settlement?.remark ?? '')
  }

  const handlePayableSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!payableTarget) return
    setSavingPayable(true)
    try {
      await salaryApi.upsertSettlement({
        member_id: payableTarget.id,
        period_start: range.period_start,
        period_end: range.period_end,
        payable_amount: parseFloat(payableAmount),
        remark: payableRemark.trim() || undefined,
      })
      showToast(`${payableTarget.name} 的应付工资已更新`, 'success')
      setPayableTarget(null)
      loadMembers()
    } catch (err: any) {
      showToast(err.message, 'error')
    } finally {
      setSavingPayable(false)
    }
  }

  const handlePayOpen = (member: MemberResponse, settlement: SalarySettlementResponse) => {
    setPaymentTarget({ member, settlement })
    setPaymentAmount(String(settlement.unpaid_amount))
    setPaymentBonus('')
    setPaymentRemark('')
  }

  const showAlerts = (alerts: string[]) => {
    const labels: Record<string, string> = {
      high_amount: '金额超过预警阈值',
      duplicate: '疑似重复提交',
      high_frequency: '提交频率异常',
    }
    alerts.forEach((alert) => showToast(labels[alert] ?? `触发风险提示：${alert}`, 'info'))
  }

  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!paymentTarget) return
    setPaying(true)
    try {
      const result = await salaryApi.paySettlement(paymentTarget.settlement.id, {
        amount: parseFloat(paymentAmount),
        bonus: paymentBonus ? parseFloat(paymentBonus) : undefined,
        remark: paymentRemark.trim() || undefined,
      })
      showAlerts(result.alerts)
      showToast(`已向 ${paymentTarget.member.name} 发放工资`, 'success')
      setPaymentTarget(null)
      loadMembers()
    } catch (err: any) {
      showToast(err.message, 'error')
    } finally {
      setPaying(false)
    }
  }

  const handleEditOpen = (member: MemberResponse) => {
    setEditMemberTarget(member)
    setEditName(member.name)
    setEditRole(member.role || '')
    setEditIsActive(member.is_active)
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editMemberTarget || !editName.trim()) return
    setEditing(true)
    try {
      await membersApi.update(editMemberTarget.id, {
        name: editName.trim(),
        role: editRole.trim() || undefined,
        is_active: editIsActive,
      })
      showToast(`成员 ${editName.trim()} 信息已更新`, 'success')
      setEditMemberTarget(null)
      loadMembers()
    } catch (err: any) {
      showToast(err.message, 'error')
    } finally {
      setEditing(false)
    }
  }

  const summaryCards = [
    { label: '本期应付', value: settlements.total_payable, color: 'var(--text-primary)', icon: ReceiptText },
    { label: '本期已付', value: settlements.total_paid, color: 'var(--color-income)', icon: Wallet },
    { label: '本期未付', value: settlements.total_unpaid, color: settlements.total_unpaid > 0 ? 'var(--color-expense)' : 'var(--text-muted)', icon: CreditCard },
  ]

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <h1 className="page-title">成员与薪资</h1>
            <p className="page-subtitle">按账期管理成员工资的应付、已付与未付</p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <label className="form-input" style={{ width: 'auto', display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 12px' }}>
              <CalendarDays size={15} style={{ color: 'var(--text-muted)' }} />
              <input
                type="month"
                value={periodMonth}
                onChange={(e) => setPeriodMonth(e.target.value || currentMonthValue())}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', fontFamily: 'inherit', outline: 'none' }}
              />
            </label>
            <button className="btn btn-primary" onClick={() => setAddMemberOpen(true)}>
              <UserPlus size={16} />新增成员
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 18 }}>
        {summaryCards.map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="glass-card" style={{ padding: '16px 18px', borderRadius: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{range.label} · {label}</span>
              <Icon size={15} style={{ color }} />
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>{money(value)}</div>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))', gap: 16 }}>
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 245, borderRadius: 16 }} />)}
        </div>
      ) : !members.length ? (
        <div className="empty-state glass-card" style={{ padding: 64 }}>
          <Users size={48} />
          <p>暂无团队成员，点击右上角添加</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))', gap: 16 }}>
          {members.map((member, i) => (
            <MemberCard
              key={member.id}
              member={member}
              settlement={getSettlement(member.id)}
              onSetPayable={handlePayableOpen}
              onPay={handlePayOpen}
              onEdit={handleEditOpen}
              delay={i * 0.06}
            />
          ))}
        </div>
      )}

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

      <Modal isOpen={!!payableTarget} onClose={() => setPayableTarget(null)} title="设置账期应付工资">
        {payableTarget && (
          <form onSubmit={handlePayableSubmit}>
            <div className="form-group">
              <label className="form-label">成员</label>
              <input className="form-input" value={`${payableTarget.name} · ${range.label}`} disabled />
            </div>
            <div className="form-group">
              <label className="form-label">应付工资 (¥) *</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0.01"
                value={payableAmount}
                onChange={(e) => setPayableAmount(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label">备注（可选）</label>
              <input
                className="form-input"
                type="text"
                maxLength={500}
                placeholder="例：基础薪资、补贴说明"
                value={payableRemark}
                onChange={(e) => setPayableRemark(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
              <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setPayableTarget(null)}>取消</button>
              <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={savingPayable}>
                {savingPayable ? '保存中...' : '保存应付'}
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal isOpen={!!paymentTarget} onClose={() => setPaymentTarget(null)} title="发放账期工资">
        {paymentTarget && (
          <form onSubmit={handlePaymentSubmit}>
            <div className="form-group">
              <label className="form-label">成员与未付金额</label>
              <input className="form-input" value={`${paymentTarget.member.name} · 未付 ${money(paymentTarget.settlement.unpaid_amount)}`} disabled />
            </div>
            <div className="form-group">
              <label className="form-label">本次发放 (¥) *</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0.01"
                max={paymentTarget.settlement.unpaid_amount}
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label">奖金 (¥，可选)</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0"
                value={paymentBonus}
                onChange={(e) => setPaymentBonus(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">备注（可选）</label>
              <input
                className="form-input"
                type="text"
                maxLength={500}
                placeholder="例：部分发放、尾款结清"
                value={paymentRemark}
                onChange={(e) => setPaymentRemark(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
              <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setPaymentTarget(null)}>取消</button>
              <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={paying}>
                {paying ? '发放中...' : '确认发放'}
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal isOpen={!!editMemberTarget} onClose={() => setEditMemberTarget(null)} title="编辑团队成员">
        {editMemberTarget && (
          <form onSubmit={handleEditSubmit}>
            <div className="form-group">
              <label className="form-label">姓名 *</label>
              <input
                className="form-input"
                type="text"
                placeholder="例：张三"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">角色（可选）</label>
              <input
                className="form-input"
                type="text"
                placeholder="例：开发、设计、运营"
                value={editRole}
                onChange={(e) => setEditRole(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">状态</label>
              <button
                type="button"
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '12px 16px', background: 'var(--bg-surface)',
                  borderRadius: 12, border: '1px solid var(--border-default)',
                  cursor: 'pointer', width: '100%', textAlign: 'left',
                }}
                onClick={() => setEditIsActive(!editIsActive)}
              >
                <div style={{
                  width: 40, height: 24, borderRadius: 12,
                  background: editIsActive ? 'var(--color-income)' : 'var(--color-expense)',
                  position: 'relative', transition: 'all 0.2s', flexShrink: 0,
                }}>
                  <div style={{
                    width: 20, height: 20, borderRadius: '50%', background: '#fff',
                    position: 'absolute', top: 2, left: editIsActive ? 18 : 2,
                    transition: 'all 0.2s', boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: editIsActive ? 'var(--color-income)' : 'var(--color-expense)' }}>
                    {editIsActive ? '在职' : '已退出'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {editIsActive ? '成员可以继续参与记账和结算' : '成员保留历史账务，但默认不参与新增选择'}
                  </div>
                </div>
              </button>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setEditMemberTarget(null)}>取消</button>
              <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={editing}>
                {editing ? '保存中...' : '保存更改'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </>
  )
}
