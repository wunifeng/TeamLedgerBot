import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { Modal } from '@/components/UI/Modal'
import { categoriesApi, expensesApi, membersApi } from '@/services/api'
import type { CategoryResponse, MemberExpenseResponse, MemberResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  onClose: () => void
  onSuccess: (expense: MemberExpenseResponse) => void
}

export function AddExpenseModal({ isOpen, onClose, onSuccess }: Props) {
  const { showToast } = useApp()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [categories, setCategories] = useState<CategoryResponse[]>([])
  const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [memberId, setMemberId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState('')
  const [remark, setRemark] = useState('')
  const [receipt, setReceipt] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    setDate(format(new Date(), 'yyyy-MM-dd')); setAmount(''); setRemark(''); setReceipt(null)
    Promise.all([membersApi.list(), categoriesApi.listExpenses()]).then(([memberRows, categoryRows]) => {
      setMembers(memberRows); setCategories(categoryRows)
      setMemberId(memberRows[0]?.id ?? ''); setCategoryId('')
    }).catch((error) => showToast(error.message, 'error'))
  }, [isOpen, showToast])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const payload = new FormData()
    payload.append('business_date', date)
    payload.append('member_id', memberId)
    payload.append('amount', amount)
    if (categoryId) payload.append('category_id', categoryId)
    if (remark) payload.append('remark', remark)
    if (receipt) payload.append('receipt', receipt)
    setLoading(true)
    try {
      onSuccess(await expensesApi.create(payload))
    } catch (error: any) {
      showToast(error.message ?? '支出提交失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="登记成员垫付">
      <form onSubmit={submit}>
        <div className="form-group"><label className="form-label">日期 *</label><input className="form-input" type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></div>
        <div className="form-group"><label className="form-label">垫付成员 *</label><select className="form-input" value={memberId} onChange={(e) => setMemberId(e.target.value)} required>{members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}</select></div>
        <div className="form-group"><label className="form-label">分类</label><select className="form-input" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}><option value="">未分类</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></div>
        <div className="form-group"><label className="form-label">金额 *</label><input className="form-input" type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required /></div>
        <div className="form-group"><label className="form-label">凭证</label><input className="form-input" type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" onChange={(e) => setReceipt(e.target.files?.[0] ?? null)} /></div>
        <div className="form-group"><label className="form-label">备注</label><input className="form-input" value={remark} onChange={(e) => setRemark(e.target.value)} maxLength={500} /></div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={onClose}>取消</button>
          <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={loading}>{loading ? '提交中...' : '登记支出'}</button>
        </div>
      </form>
    </Modal>
  )
}
