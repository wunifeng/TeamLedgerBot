import { useEffect, useState } from 'react'
import { Modal } from '@/components/UI/Modal'
import { expensesApi, categoriesApi } from '@/services/api'
import type { CategoryResponse, MemberExpenseResponse, MemberExpenseUpdate } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  expense: MemberExpenseResponse | null
  onClose: () => void
  onSuccess: (updated: MemberExpenseResponse) => void
}

export function EditExpenseModal({ isOpen, expense, onClose, onSuccess }: Props) {
  const { showToast } = useApp()
  const [categories, setCategories] = useState<CategoryResponse[]>([])
  const [form, setForm] = useState({ amount: '', category_id: '', remark: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen || !expense) return
    setForm({
      amount: String(expense.amount),
      category_id: expense.category_id ?? '',
      remark: expense.remark ?? '',
    })
    categoriesApi.listExpenses()
      .then(setCategories)
      .catch(() => showToast('加载分类失败', 'error'))
  }, [isOpen, expense, showToast])

  const field = (name: keyof typeof form, value: string) =>
    setForm((cur) => ({ ...cur, [name]: value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!expense) return
    setLoading(true)
    try {
      const payload: MemberExpenseUpdate = {
        amount: Number(form.amount),
        category_id: form.category_id || null,
        remark: form.remark || null,
      }
      const updated = await expensesApi.patch(expense.id, payload)
      onSuccess(updated)
    } catch (err: any) {
      showToast(err.message ?? '修改失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!expense) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`编辑支出 — ${expense.member_name} · ${expense.business_date}`}>
      <form onSubmit={submit}>
        <div className="form-group">
          <label className="form-label">金额 *</label>
          <input
            id="edit-expense-amount"
            className="form-input"
            type="number"
            min="0.01"
            step="0.01"
            value={form.amount}
            onChange={(e) => field('amount', e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">分类</label>
          <select
            id="edit-expense-category"
            className="form-input"
            value={form.category_id}
            onChange={(e) => field('category_id', e.target.value)}
          >
            <option value="">未分类</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">备注</label>
          <input
            id="edit-expense-remark"
            className="form-input"
            maxLength={500}
            value={form.remark}
            onChange={(e) => field('remark', e.target.value)}
          />
        </div>
        <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={onClose}>取消</button>
          <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={loading}>
            {loading ? '保存中...' : '保存修改'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
