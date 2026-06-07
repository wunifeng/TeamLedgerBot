import { useCallback, useEffect, useState } from 'react'
import { ArrowLeftRight, Ban, CalendarDays, CreditCard, KeyRound, Plus, Shield, Trash2, UserPlus, Wallet } from 'lucide-react'
import { Modal } from '@/components/UI/Modal'
import { authApi, bankrollApi, membersApi, salaryApi } from '@/services/api'
import type {
  BankrollAdjustmentDirection,
  BankrollEntryListResponse,
  BankrollEntryResponse,
  BankrollEntryType,
  BankrollSummaryResponse,
  MemberResponse,
  SalaryPaymentItem,
  SalarySettlementListResponse,
  SalarySettlementResponse,
} from '@/types/api'
import { useApp } from '@/context/AppContext'

const emptySalary: SalarySettlementListResponse = { items: [], total_payable: 0, total_paid: 0, total_unpaid: 0 }
const emptyBankrollSummary: BankrollSummaryResponse = { items: [], total_balance: 0 }
const emptyBankrollEntries: BankrollEntryListResponse = { items: [], total: 0, page: 1, limit: 15, pages: 1 }
const currentMonth = () => new Date().toISOString().slice(0, 7)
const todayDate = () => new Date().toISOString().slice(0, 10)
const range = (month: string) => {
  const [year, value] = month.split('-').map(Number)
  return { period_start: `${month}-01`, period_end: `${month}-${String(new Date(year, value, 0).getDate()).padStart(2, '0')}` }
}
const money = (value: number) => `¥${new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2 }).format(Number(value || 0))}`
const timeText = (value: string) => new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
}).format(new Date(value))

const bankrollTypeLabels: Record<BankrollEntryType, string> = {
  initial: '初始',
  top_up: '补充',
  return: '退回',
  adjustment: '调整',
}

const bankrollDirectionLabels: Record<BankrollAdjustmentDirection, string> = {
  increase: '增加',
  decrease: '减少',
}

interface VoidTarget {
  settlement: SalarySettlementResponse
  payment: SalaryPaymentItem
}

interface BankrollFormState {
  business_date: string
  member_id: string
  entry_type: BankrollEntryType
  amount: string
  adjustment_direction: BankrollAdjustmentDirection
  remark: string
}

const initialBankrollForm = (): BankrollFormState => ({
  business_date: todayDate(),
  member_id: '',
  entry_type: 'top_up',
  amount: '',
  adjustment_direction: 'increase',
  remark: '',
})

export default function MembersPage() {
  const { showToast, currentMember } = useApp()
  const [activeTab, setActiveTab] = useState<'salary' | 'bankroll'>('salary')
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [settlements, setSettlements] = useState<SalarySettlementListResponse>(emptySalary)
  const [bankrollSummary, setBankrollSummary] = useState<BankrollSummaryResponse>(emptyBankrollSummary)
  const [bankrollEntries, setBankrollEntries] = useState<BankrollEntryListResponse>(emptyBankrollEntries)
  const [bankrollPage, setBankrollPage] = useState(1)
  const [bankrollMemberFilter, setBankrollMemberFilter] = useState('')
  const [bankrollTypeFilter, setBankrollTypeFilter] = useState<BankrollEntryType | ''>('')
  const [bankrollIncludeVoided, setBankrollIncludeVoided] = useState(false)
  const [month, setMonth] = useState(currentMonth())
  const [addOpen, setAddOpen] = useState(false)
  const [name, setName] = useState('')
  const [role, setRole] = useState('')
  const [payment, setPayment] = useState<SalarySettlementResponse | null>(null)
  const [amount, setAmount] = useState('')
  const [remark, setRemark] = useState('')
  const [voidTarget, setVoidTarget] = useState<VoidTarget | null>(null)
  const [voidReason, setVoidReason] = useState('')
  const [bankrollOpen, setBankrollOpen] = useState(false)
  const [bankrollForm, setBankrollForm] = useState<BankrollFormState>(initialBankrollForm)
  const [bankrollVoidTarget, setBankrollVoidTarget] = useState<BankrollEntryResponse | null>(null)
  const [bankrollVoidReason, setBankrollVoidReason] = useState('')

  // PIN 设置状态
  const [pinTarget, setPinTarget] = useState<MemberResponse | null>(null)
  const [newPin, setNewPin] = useState('')
  const [pinLoading, setPinLoading] = useState(false)

  const load = useCallback(async () => {
    try {
      const [memberRows, settlementRows, nextBankrollSummary, nextBankrollEntries] = await Promise.all([
        membersApi.list(true),
        salaryApi.listSettlements({ ...range(month), include_inactive: true }),
        bankrollApi.summary(),
        bankrollApi.entries({
          member_id: bankrollMemberFilter || undefined,
          entry_type: bankrollTypeFilter || undefined,
          include_voided: bankrollIncludeVoided,
          page: bankrollPage,
          limit: 15,
        }),
      ])
      setMembers(memberRows)
      setSettlements(settlementRows)
      setBankrollSummary(nextBankrollSummary)
      setBankrollEntries(nextBankrollEntries)
    } catch (error: any) { showToast(error.message, 'error') }
  }, [bankrollIncludeVoided, bankrollMemberFilter, bankrollPage, bankrollTypeFilter, month, showToast])
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

  const voidPayment = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!voidTarget) return
    try {
      await salaryApi.voidPayment(voidTarget.payment.id, { reason: voidReason || undefined })
      setVoidTarget(null); setVoidReason(''); showToast('工资发放记录已作废', 'success'); load()
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

  const openBankrollModal = () => {
    const firstActiveMember = members.find((member) => member.is_active)?.id ?? members[0]?.id ?? ''
    setBankrollForm({ ...initialBankrollForm(), member_id: firstActiveMember })
    setBankrollOpen(true)
  }

  const createBankrollEntry = async (event: React.FormEvent) => {
    event.preventDefault()
    try {
      const trimmedRemark = bankrollForm.remark.trim()
      await bankrollApi.create({
        business_date: bankrollForm.business_date,
        member_id: bankrollForm.member_id,
        entry_type: bankrollForm.entry_type,
        amount: Number(bankrollForm.amount),
        adjustment_direction: bankrollForm.entry_type === 'adjustment' ? bankrollForm.adjustment_direction : undefined,
        remark: trimmedRemark || undefined,
      })
      setBankrollOpen(false)
      setBankrollPage(1)
      showToast('Bankroll 变动已登记', 'success')
      load()
    } catch (error: any) { showToast(error.message, 'error') }
  }

  const voidBankrollEntry = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!bankrollVoidTarget) return
    try {
      await bankrollApi.voidEntry(bankrollVoidTarget.id, { reason: bankrollVoidReason })
      setBankrollVoidTarget(null)
      setBankrollVoidReason('')
      showToast('Bankroll 变动记录已作废', 'success')
      load()
    } catch (error: any) { showToast(error.message, 'error') }
  }

  // 是否可以设置某成员的 PIN（管理员可设置所有人，普通成员只能设自己）
  const canSetPin = (member: MemberResponse) =>
    !!(currentMember?.is_admin || currentMember?.id === member.id)

  // 成员停用保留历史流水、垫付和工资记录，仅管理员可操作他人。
  const canDeactivateMember = (member: MemberResponse) =>
    !!(currentMember?.is_admin && currentMember.id !== member.id && member.is_active)

  const deactivateMember = async (member: MemberResponse) => {
    if (!confirm(`确定停用 ${member.name} 吗？历史流水、垫付、工资和 bankroll 记录会保留。`)) return
    try {
      await membersApi.delete(member.id)
      showToast(`${member.name} 已停用`, 'success')
      await load()
    } catch (error: any) {
      showToast(error.message ?? '停用成员失败', 'error')
    }
  }

  const selectedBankrollMember = members.find((member) => member.id === bankrollForm.member_id)
  const activeBankrollTotal = bankrollSummary.items
    .filter((item) => item.is_active)
    .reduce((sum, item) => sum + Number(item.balance || 0), 0)
  const negativeBankrollCount = bankrollSummary.items.filter((item) => Number(item.balance || 0) < 0).length

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 18, flexWrap: 'wrap' }}>
        <div>
          <h1 className="page-title">成员管理</h1>
          <p className="page-subtitle">成员工资发放与团队 bankroll 持有追踪</p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {activeTab === 'salary' && (
            <label className="form-input" style={{ display: 'flex', alignItems: 'center', gap: 8, width: 'auto' }}>
              <CalendarDays size={15} />
              <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} style={{ background: 'transparent', color: 'inherit', border: 0 }} />
            </label>
          )}
          {activeTab === 'bankroll' && currentMember?.is_admin && (
            <button className="btn btn-primary" onClick={openBankrollModal}><Wallet size={16} />登记变动</button>
          )}
          <button className="btn btn-primary" onClick={() => setAddOpen(true)}><UserPlus size={16} />新增成员</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 18, flexWrap: 'wrap' }}>
        <button
          className={`btn ${activeTab === 'salary' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('salary')}
          type="button"
        >
          <CreditCard size={15} />工资
        </button>
        <button
          className={`btn ${activeTab === 'bankroll' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('bankroll')}
          type="button"
        >
          <Wallet size={15} />Bankroll
        </button>
      </div>

      {activeTab === 'salary' ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 12, marginBottom: 18 }}>
            {[['本期应付', settlements.total_payable], ['本期已付', settlements.total_paid], ['本期未付', settlements.total_unpaid]].map(([label, value]) => (
              <div className="glass-card" style={{ padding: 18 }} key={String(label)}>
                <div className="stat-label">{label}</div>
                <div className="stat-value">{money(Number(value))}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 14 }}>
            {members.map((member) => {
              const settlement = settlements.items.find((item) => item.member_id === member.id)
              const payments = settlement?.payments ?? []
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

                  {payments.length > 0 && (
                    <div style={{ borderTop: '1px solid var(--border-default)', paddingTop: 12, marginBottom: 14 }}>
                      <div className="stat-label" style={{ marginBottom: 8 }}>发放明细</div>
                      <div style={{ display: 'grid', gap: 8 }}>
                        {payments.map((item) => {
                          const voided = !!item.voided_at
                          const note = voided ? item.void_reason || item.remark : item.remark
                          return (
                            <div
                              key={item.id}
                              style={{
                                display: 'grid',
                                gridTemplateColumns: currentMember?.is_admin && !voided ? '1fr auto' : '1fr',
                                gap: 8,
                                alignItems: 'center',
                                opacity: voided ? 0.62 : 1,
                              }}
                            >
                              <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                  <strong>{money(item.amount)}</strong>
                                  <span className="badge">{voided ? '已作废' : '有效'}</span>
                                  <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{timeText(item.paid_at)}</span>
                                </div>
                                {note && (
                                  <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 3 }}>
                                    {note}
                                  </div>
                                )}
                              </div>
                              {currentMember?.is_admin && !voided && (
                                <button
                                  className="btn btn-ghost btn-sm"
                                  onClick={() => { if (settlement) { setVoidTarget({ settlement, payment: item }); setVoidReason('') } }}
                                  title="作废发放记录"
                                  type="button"
                                >
                                  <Ban size={14} />作废
                                </button>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {currentMember?.is_admin && (
                      <button
                        className="btn btn-ghost btn-sm"
                        style={{ flex: '1 1 110px' }}
                        disabled={!settlement || settlement.unpaid_amount <= 0}
                        onClick={() => { if (settlement) { setPayment(settlement); setAmount(String(settlement.unpaid_amount)); setRemark('') } }}
                      >
                        <CreditCard size={14} />登记发放
                      </button>
                    )}
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
        </>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 12, marginBottom: 18 }}>
            <div className="glass-card" style={{ padding: 18 }}>
              <div className="stat-label">成员持有合计</div>
              <div className="stat-value">{money(bankrollSummary.total_balance)}</div>
            </div>
            <div className="glass-card" style={{ padding: 18 }}>
              <div className="stat-label">在职成员持有</div>
              <div className="stat-value">{money(activeBankrollTotal)}</div>
            </div>
            <div className="glass-card" style={{ padding: 18 }}>
              <div className="stat-label">负余额成员</div>
              <div className="stat-value" style={{ color: negativeBankrollCount ? 'var(--color-expense)' : 'var(--color-income)' }}>{negativeBankrollCount}</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 12, marginBottom: 18 }}>
            {bankrollSummary.items.map((item) => (
              <div className="glass-card" style={{ padding: 16 }} key={item.member_id}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 10 }}>
                  <div>
                    <strong>{item.member_name}</strong>
                    <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{item.role ?? '团队成员'}</div>
                  </div>
                  <span className="badge">{item.is_active ? '在职' : '已停用'}</span>
                </div>
                <div className="stat-value" style={{ color: Number(item.balance) >= 0 ? 'var(--color-income)' : 'var(--color-expense)' }}>
                  {money(item.balance)}
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 12, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {currentMember?.is_admin && (
                <select
                  className="form-input"
                  value={bankrollMemberFilter}
                  onChange={(event) => { setBankrollMemberFilter(event.target.value); setBankrollPage(1) }}
                  style={{ width: 160 }}
                >
                  <option value="">全部成员</option>
                  {members.map((member) => (
                    <option key={member.id} value={member.id}>{member.name}{member.is_active ? '' : '（停用）'}</option>
                  ))}
                </select>
              )}
              <select
                className="form-input"
                value={bankrollTypeFilter}
                onChange={(event) => { setBankrollTypeFilter(event.target.value as BankrollEntryType | ''); setBankrollPage(1) }}
                style={{ width: 140 }}
              >
                <option value="">全部类型</option>
                {(Object.keys(bankrollTypeLabels) as BankrollEntryType[]).map((type) => (
                  <option key={type} value={type}>{bankrollTypeLabels[type]}</option>
                ))}
              </select>
              <label className="form-input" style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={bankrollIncludeVoided}
                  onChange={(event) => { setBankrollIncludeVoided(event.target.checked); setBankrollPage(1) }}
                />
                含作废
              </label>
            </div>
          </div>

          <div className="glass-card" style={{ overflowX: 'auto' }}>
            {!bankrollEntries.items.length ? <div className="empty-state">暂无 bankroll 变动</div> : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>日期</th><th>成员</th><th>类型</th><th>金额</th><th>余额影响</th><th>状态</th><th>备注</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {bankrollEntries.items.map((entry) => {
                    const voided = !!entry.voided_at
                    return (
                      <tr key={entry.id} style={{ opacity: voided ? 0.62 : 1 }}>
                        <td>{entry.business_date}</td>
                        <td>{entry.member_name}</td>
                        <td>
                          {bankrollTypeLabels[entry.entry_type]}
                          {entry.adjustment_direction ? ` · ${bankrollDirectionLabels[entry.adjustment_direction]}` : ''}
                        </td>
                        <td style={{ fontWeight: 700 }}>{money(entry.amount)}</td>
                        <td style={{ color: Number(entry.signed_amount) >= 0 ? 'var(--color-income)' : 'var(--color-expense)', fontWeight: 700 }}>
                          {money(entry.signed_amount)}
                        </td>
                        <td><span className="badge">{voided ? '已作废' : '有效'}</span></td>
                        <td>{voided ? entry.void_reason ?? entry.remark ?? '—' : entry.remark ?? '—'}</td>
                        <td>
                          {currentMember?.is_admin && !voided && (
                            <button
                              className="btn btn-danger btn-sm"
                              type="button"
                              onClick={() => { setBankrollVoidTarget(entry); setBankrollVoidReason('') }}
                              title="作废 bankroll 变动"
                            >
                              <Ban size={13} />作废
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
            <button className="btn btn-ghost btn-sm" disabled={bankrollPage <= 1} onClick={() => setBankrollPage((page) => Math.max(1, page - 1))}>
              上一页
            </button>
            <span style={{ color: 'var(--text-muted)', fontSize: 13, alignSelf: 'center' }}>
              {bankrollEntries.page} / {bankrollEntries.pages}
            </span>
            <button className="btn btn-ghost btn-sm" disabled={bankrollPage >= bankrollEntries.pages} onClick={() => setBankrollPage((page) => page + 1)}>
              下一页
            </button>
          </div>
        </>
      )}

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

      <Modal isOpen={!!voidTarget} onClose={() => { setVoidTarget(null); setVoidReason('') }} title="作废工资发放">
        {voidTarget && (
          <form onSubmit={voidPayment}>
            <div className="form-group">
              <label className="form-label">成员与账期</label>
              <input className="form-input" value={`${voidTarget.settlement.member_name} · ${voidTarget.settlement.period_start} 至 ${voidTarget.settlement.period_end}`} disabled />
            </div>
            <div className="form-group">
              <label className="form-label">作废金额</label>
              <input className="form-input" value={money(voidTarget.payment.amount)} disabled />
            </div>
            <div className="form-group">
              <label className="form-label">作废原因</label>
              <input className="form-input" value={voidReason} onChange={(e) => setVoidReason(e.target.value)} maxLength={500} />
            </div>
            <button className="btn btn-danger" type="submit"><Ban size={14} />确认作废</button>
          </form>
        )}
      </Modal>

      <Modal isOpen={bankrollOpen} onClose={() => setBankrollOpen(false)} title="登记 Bankroll 变动">
        <form onSubmit={createBankrollEntry}>
          <div className="form-group">
            <label className="form-label">业务日期 *</label>
            <input
              className="form-input"
              type="date"
              value={bankrollForm.business_date}
              onChange={(e) => setBankrollForm((form) => ({ ...form, business_date: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">成员 *</label>
            <select
              className="form-input"
              value={bankrollForm.member_id}
              onChange={(e) => setBankrollForm((form) => ({ ...form, member_id: e.target.value }))}
              required
            >
              {members.map((member) => (
                <option key={member.id} value={member.id}>{member.name}{member.is_active ? '' : '（停用）'}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">类型 *</label>
            <select
              className="form-input"
              value={bankrollForm.entry_type}
              onChange={(e) => setBankrollForm((form) => ({ ...form, entry_type: e.target.value as BankrollEntryType }))}
              required
            >
              <option value="initial" disabled={selectedBankrollMember && !selectedBankrollMember.is_active}>初始</option>
              <option value="top_up" disabled={selectedBankrollMember && !selectedBankrollMember.is_active}>补充</option>
              <option value="return">退回</option>
              <option value="adjustment">调整</option>
            </select>
          </div>
          {bankrollForm.entry_type === 'adjustment' && (
            <div className="form-group">
              <label className="form-label">调整方向 *</label>
              <select
                className="form-input"
                value={bankrollForm.adjustment_direction}
                onChange={(e) => setBankrollForm((form) => ({ ...form, adjustment_direction: e.target.value as BankrollAdjustmentDirection }))}
                required
              >
                <option value="increase">增加</option>
                <option value="decrease">减少</option>
              </select>
            </div>
          )}
          <div className="form-group">
            <label className="form-label">金额 *</label>
            <input
              className="form-input"
              type="number"
              min="0.01"
              step="0.01"
              value={bankrollForm.amount}
              onChange={(e) => setBankrollForm((form) => ({ ...form, amount: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">{bankrollForm.entry_type === 'adjustment' ? '原因 *' : '备注'}</label>
            <input
              className="form-input"
              value={bankrollForm.remark}
              onChange={(e) => setBankrollForm((form) => ({ ...form, remark: e.target.value }))}
              maxLength={500}
              required={bankrollForm.entry_type === 'adjustment'}
            />
          </div>
          <button className="btn btn-primary" type="submit"><ArrowLeftRight size={14} />确认登记</button>
        </form>
      </Modal>

      <Modal isOpen={!!bankrollVoidTarget} onClose={() => { setBankrollVoidTarget(null); setBankrollVoidReason('') }} title="作废 Bankroll 变动">
        {bankrollVoidTarget && (
          <form onSubmit={voidBankrollEntry}>
            <div className="form-group">
              <label className="form-label">记录</label>
              <input
                className="form-input"
                value={`${bankrollVoidTarget.member_name} · ${bankrollTypeLabels[bankrollVoidTarget.entry_type]} · ${money(bankrollVoidTarget.amount)}`}
                disabled
              />
            </div>
            <div className="form-group">
              <label className="form-label">作废原因 *</label>
              <input
                className="form-input"
                value={bankrollVoidReason}
                onChange={(e) => setBankrollVoidReason(e.target.value)}
                maxLength={500}
                required
              />
            </div>
            <button className="btn btn-danger" type="submit"><Ban size={14} />确认作废</button>
          </form>
        )}
      </Modal>

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
