import { useEffect, useState } from 'react'
import { Modal } from '@/components/UI/Modal'
import { transactionsApi, membersApi, categoriesApi } from '@/services/api'
import type { MemberResponse, CategoryResponse, TransactionWriteResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  onClose: () => void
  onSuccess: (result?: TransactionWriteResponse) => void
  initialTab?: TxTab
  initialMemberId?: string
}

type TxTab = 'income' | 'expense' | 'salary'

export function AddTransactionModal({
  isOpen,
  onClose,
  onSuccess,
  initialTab = 'income',
  initialMemberId,
}: Props) {
  const { showToast } = useApp()
  const [tab, setTab] = useState<TxTab>('income')
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [categories, setCategories] = useState<CategoryResponse[]>([])
  const [loading, setLoading] = useState(false)

  const [form, setForm] = useState({
    amount: '',
    salary_amount: '',
    bonus: '',
    member_id: '',
    category_id: '',
    remark: '',
  })

  useEffect(() => {
    if (!isOpen) return
    setTab(initialTab)
    setForm({
      amount: '',
      salary_amount: '',
      bonus: '',
      member_id: initialMemberId ?? '',
      category_id: '',
      remark: '',
    })
    Promise.all([membersApi.list(), categoriesApi.list()]).then(([m, c]) => {
      setMembers(m)
      setCategories(c)
      if (m.length) {
        const selectedMember = initialMemberId && m.some((item) => item.id === initialMemberId)
          ? initialMemberId
          : m[0].id
        setForm((f) => ({ ...f, member_id: selectedMember }))
      }
    })
  }, [isOpen, initialTab, initialMemberId])

  const filteredCategories = categories.filter(
    (c) => c.type === tab
  )

  const showAlerts = (alerts: string[]) => {
    const labels: Record<string, string> = {
      high_amount: '金额超过预警阈值',
      duplicate: '疑似重复提交',
      high_frequency: '提交频率异常',
    }
    alerts.forEach((alert) => showToast(labels[alert] ?? `触发风险提示：${alert}`, 'info'))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.member_id) return showToast('请选择成员', 'error')

    setLoading(true)
    try {
      let result: TransactionWriteResponse
      if (tab === 'income') {
        result = await transactionsApi.createIncome({
          amount: parseFloat(form.amount),
          member_id: form.member_id,
          category_id: form.category_id || undefined,
          remark: form.remark || undefined,
        })
      } else if (tab === 'expense') {
        result = await transactionsApi.createExpense({
          amount: parseFloat(form.amount),
          member_id: form.member_id,
          category_id: form.category_id || undefined,
          remark: form.remark || undefined,
        })
      } else {
        result = await transactionsApi.createSalary({
          salary_amount: parseFloat(form.salary_amount),
          bonus: form.bonus ? parseFloat(form.bonus) : undefined,
          member_id: form.member_id,
          remark: form.remark || undefined,
        })
      }
      showAlerts(result.alerts)
      onSuccess(result)
    } catch (err: any) {
      showToast(err.message ?? '提交失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  const tabStyle = (active: boolean, color: string) => ({
    flex: 1,
    padding: '8px 4px',
    background: active ? `${color}20` : 'transparent',
    border: `1px solid ${active ? color + '40' : 'transparent'}`,
    borderRadius: 8,
    color: active ? color : 'var(--text-muted)',
    fontSize: 13,
    fontWeight: active ? 600 : 400,
    cursor: 'pointer',
    transition: 'all 0.15s',
    fontFamily: 'inherit',
  })

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="新增交易记录">
      {/* Type tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        <button type="button" style={tabStyle(tab === 'income', 'var(--color-income)')} onClick={() => setTab('income')}>💰 收入</button>
        <button type="button" style={tabStyle(tab === 'expense', 'var(--color-expense)')} onClick={() => setTab('expense')}>💸 支出</button>
        <button type="button" style={tabStyle(tab === 'salary', 'var(--color-salary)')} onClick={() => setTab('salary')}>💵 薪资</button>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Member selector */}
        <div className="form-group">
          <label className="form-label">成员</label>
          <select
            className="form-input"
            value={form.member_id}
            onChange={(e) => setForm((f) => ({ ...f, member_id: e.target.value }))}
            required
          >
            {members.map((m) => (
              <option key={m.id} value={m.id}>{m.name}{m.role ? ` · ${m.role}` : ''}</option>
            ))}
          </select>
        </div>

        {/* Amount fields */}
        {tab === 'salary' ? (
          <>
            <div className="form-group">
              <label className="form-label">薪资金额 (¥)</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={form.salary_amount}
                onChange={(e) => setForm((f) => ({ ...f, salary_amount: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">奖金 (¥，可选)</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={form.bonus}
                onChange={(e) => setForm((f) => ({ ...f, bonus: e.target.value }))}
              />
            </div>
          </>
        ) : (
          <div className="form-group">
            <label className="form-label">金额 (¥)</label>
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0.00"
              value={form.amount}
              onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
              required
            />
          </div>
        )}

        {tab !== 'salary' && (
          <div className="form-group">
            <label className="form-label">分类（可选）</label>
            <select
              className="form-input"
              value={form.category_id}
              onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}
            >
              <option value="">-- 不选分类 --</option>
              {filteredCategories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Remark */}
        <div className="form-group">
          <label className="form-label">备注（可选）</label>
          <input
            className="form-input"
            type="text"
            placeholder="添加备注..."
            maxLength={500}
            value={form.remark}
            onChange={(e) => setForm((f) => ({ ...f, remark: e.target.value }))}
          />
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={onClose}>
            取消
          </button>
          <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={loading}>
            {loading ? '提交中...' : '确认提交'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
