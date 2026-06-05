import { useCallback, useEffect, useState } from 'react'
import { CalendarDays, CreditCard, KeyRound, Plus, Shield, Trash2, UserPlus, Wallet } from 'lucide-react'
import { Modal } from '@/components/UI/Modal'
import { authApi, membersApi, salaryApi } from '@/services/api'
import type { MemberResponse, SalarySettlementListResponse, SalarySettlementResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

const empty: SalarySettlementListResponse = { items: [], total_payable: 0, total_paid: 0, total_unpaid: 0 }
const currentMonth = () => new Date().toISOString().slice(0, 7)
const range = (month: string) => {
  const [year, value] = month.split('-').map(Number)
  return { period_start: `${month}-01`, period_end: `${month}-${String(new Date(year, value, 0).getDate()).padStart(2, '0')}` }
}
const money = (value: number) => `¥${new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2 }).format(value || 0)}`

export default function MembersPage() {
  const { showToast, currentMember } = useApp()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [settlements, setSettlements] = useState<SalarySettlementListResponse>(empty)
  const [month, setMonth] = useState(currentMonth())
  const [addOpen, setAddOpen] = useState(false)
  const [name, setName] = useState('')
  const [role, setRole] = useState('')
  const [payment, setPayment] = useState<SalarySettlementResponse | null>(null)
  const [amount, setAmount] = useState('')
  const [remark, setRemark] = useState('')

  // PIN 设置状态
  const [pinTarget, setPinTarget] = useState<MemberResponse | null>(null)
  const [newPin, setNewPin] = useState('')
  const [pinLoading, setPinLoading] = useState(false)

  const load = useCallback(async () => {
    try {
      const [memberRows, settlementRows] = await Promise.all([
        membersApi.list(true),
        salaryApi.listSettlements({ ...range(month), include_inactive: true }),
      ])
      setMembers(memberRows)
      setSettlements(settlementRows)
    } catch (error: any) { showToast(error.message, 'error') }
  }, [month, showToast])
  useEffect(() => { load() }, [load])

  const addMember = async (event: React.FormEvent) => {
    event.preventDefault()
    try {
      await membersApi.create({ name, role: role || undefined })
      setAddOpen(false); setName(''); setRole(''); load()
    } catch (error: any) { showToast(error.message, 'error') }
  }

  const pay = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!payment) return
    try {
      await salaryApi.paySettlement(payment.id, { amount: Number(amount), remark: remark || undefined })
      setPayment(null); showToast('工资发放已登记', 'success'); load()
    } catch (error: any) { showToast(error.message, 'error') }
  }

  const setPin = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!pinTarget) return
    setPinLoading(true)
    try {
      await authApi.setPin(pinTarget.id, newPin)
      showToast(`${pinTarget.name} 的 PIN 已设置`, 'success')
      setPinTarget(null); setNewPin('')
    } catch (error: any) {
      showToast(error.message ?? '设置 PIN 失败', 'error')
    } finally {
      setPinLoading(false)
    }
  }

  // 是否可以设置某成员的 PIN（管理员可设置所有人，普通成员只能设自己）
  const canSetPin = (member: MemberResponse) =>
    !!(currentMember?.is_admin || currentMember?.id === member.id)

  // 成员停用保留历史流水、垫付和工资记录，仅管理员可操作他人。
  const canDeactivateMember = (member: MemberResponse) =>
    !!(currentMember?.is_admin && currentMember.id !== member.id && member.is_active)

  const deactivateMember = async (member: MemberResponse) => {
    if (!confirm(`确定停用 ${member.name} 吗？历史流水、垫付和工资记录会保留。`)) return
    try {
      await membersApi.delete(member.id)
      showToast(`${member.name} 已停用`, 'success')
      await load()
    } catch (error: any) {
      showToast(error.message ?? '停用成员失败', 'error')
    }
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div>
          <h1 className="page-title">成员与工资</h1>
          <p className="page-subtitle">应付工资由每日流水自动计提，按自然月登记实际发放</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <label className="form-input" style={{ display: 'flex', alignItems: 'center', gap: 8, width: 'auto' }}>
            <CalendarDays size={15} />
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} style={{ background: 'transparent', color: 'inherit', border: 0 }} />
          </label>
          <button className="btn btn-primary" onClick={() => setAddOpen(true)}><UserPlus size={16} />新增成员</button>
        </div>
      </div>

      {/* 汇总卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 12, marginBottom: 18 }}>
        {[['本期应付', settlements.total_payable], ['本期已付', settlements.total_paid], ['本期未付', settlements.total_unpaid]].map(([label, value]) => (
          <div className="glass-card" style={{ padding: 18 }} key={String(label)}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{money(Number(value))}</div>
          </div>
        ))}
      </div>

      {/* 成员卡片列表 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 14 }}>
        {members.map((member) => {
          const settlement = settlements.items.find((item) => item.member_id === member.id)
          return (
            <div className="glass-card" style={{ padding: 18 }} key={member.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <strong>{member.name}</strong>
                    {member.is_admin && (
                      <span title="管理员" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 3,
                        fontSize: 11, fontWeight: 600, padding: '2px 6px', borderRadius: 8,
                        background: 'var(--color-accent)20', color: 'var(--color-accent)',
                      }}>
                        <Shield size={10} /> 管理员
                      </span>
                    )}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{member.role ?? '团队成员'}</div>
                </div>
                <span className="badge">{member.is_active ? '在职' : '已停用'}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 14 }}>
                <div><div className="stat-label">应付</div><strong>{money(settlement?.payable_amount ?? 0)}</strong></div>
                <div><div className="stat-label">已付</div><strong>{money(settlement?.paid_amount ?? 0)}</strong></div>
                <div><div className="stat-label">未付</div><strong>{money(settlement?.unpaid_amount ?? 0)}</strong></div>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                <button
                  className="btn btn-ghost btn-sm"
                  style={{ flex: '1 1 110px' }}
                  disabled={!settlement || settlement.unpaid_amount <= 0}
                  onClick={() => { if (settlement) { setPayment(settlement); setAmount(String(settlement.unpaid_amount)); setRemark('') } }}
                >
                  <CreditCard size={14} />登记发放
                </button>
                {canSetPin(member) && (
                  <button
                    className="btn btn-ghost btn-sm"
                    style={{ flex: '1 1 110px' }}
                    onClick={() => { setPinTarget(member); setNewPin('') }}
                    title="设置登录 PIN"
                  >
                    <KeyRound size={14} />设置 PIN
                  </button>
                )}
                {canDeactivateMember(member) && (
                  <button
                    className="btn btn-danger btn-sm"
                    style={{ flex: '1 1 110px' }}
                    onClick={() => deactivateMember(member)}
                    title="停用成员并保留历史记录"
                  >
                    <Trash2 size={14} />停用
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* 新增成员 Modal */}
      <Modal isOpen={addOpen} onClose={() => setAddOpen(false)} title="新增成员">
        <form onSubmit={addMember}>
          <div className="form-group">
            <label className="form-label">姓名 *</label>
            <input className="form-input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">角色</label>
            <input className="form-input" value={role} onChange={(e) => setRole(e.target.value)} />
          </div>
          <button className="btn btn-primary" type="submit"><Plus size={14} />添加成员</button>
        </form>
      </Modal>

      {/* 工资发放 Modal */}
      <Modal isOpen={!!payment} onClose={() => setPayment(null)} title="登记工资发放">
        {payment && (
          <form onSubmit={pay}>
            <div className="form-group">
              <label className="form-label">成员与账期</label>
              <input className="form-input" value={`${payment.member_name} · ${payment.period_start} 至 ${payment.period_end}`} disabled />
            </div>
            <div className="form-group">
              <label className="form-label">本次发放 *</label>
              <input className="form-input" type="number" min="0.01" max={payment.unpaid_amount} step="0.01"
                value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">备注</label>
              <input className="form-input" value={remark} onChange={(e) => setRemark(e.target.value)} />
            </div>
            <button className="btn btn-primary" type="submit"><Wallet size={14} />确认发放</button>
          </form>
        )}
      </Modal>

      {/* 设置 PIN Modal */}
      <Modal isOpen={!!pinTarget} onClose={() => { setPinTarget(null); setNewPin('') }} title={`设置 PIN — ${pinTarget?.name ?? ''}`}>
        <form onSubmit={setPin}>
          <div className="form-group">
            <label className="form-label">新 PIN（4~8 位数字）</label>
            <input
              id="set-pin-input"
              className="form-input"
              type="password"
              inputMode="numeric"
              pattern="[0-9]{4,8}"
              minLength={4}
              maxLength={8}
              placeholder="输入 4~8 位纯数字"
              value={newPin}
              onChange={(e) => setNewPin(e.target.value.replace(/\D/g, ''))}
              required
              autoComplete="new-password"
            />
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>
              PIN 将用于该成员的登录验证，请妥善保管。
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => { setPinTarget(null); setNewPin('') }}>取消</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={pinLoading}>
              <KeyRound size={14} />{pinLoading ? '设置中...' : '确认设置'}
            </button>
          </div>
        </form>
      </Modal>
    </>
  )
}
