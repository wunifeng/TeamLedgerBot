import { useCallback, useEffect, useState } from 'react'
import { FileText, Plus, Receipt, Trash2 } from 'lucide-react'
import { AddExpenseModal } from '@/components/Forms/AddExpenseModal'
import { expensesApi } from '@/services/api'
import type { MemberExpenseListResponse, MemberExpenseResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

function money(value: number) {
  return `¥${new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2 }).format(value)}`
}

export default function ExpensesPage() {
  const { showToast } = useApp()
  const [data, setData] = useState<MemberExpenseListResponse | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const load = useCallback(async () => {
    try { setData(await expensesApi.list()) } catch (error: any) { showToast(error.message, 'error') }
  }, [showToast])
  useEffect(() => { load() }, [load])

  const toggle = async (expense: MemberExpenseResponse) => {
    try { await expensesApi.setReimbursed(expense.id, !expense.reimbursed); load() } catch (error: any) { showToast(error.message, 'error') }
  }
  const remove = async (expense: MemberExpenseResponse) => {
    if (!confirm(`确定删除 ${expense.member_name} 的垫付支出吗？`)) return
    try { await expensesApi.delete(expense.id); load() } catch (error: any) { showToast(error.message, 'error') }
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div><h1 className="page-title">成员垫付</h1><p className="page-subtitle">登记团队开支凭证并跟踪报销状态</p></div>
        <button className="btn btn-primary" onClick={() => setModalOpen(true)}><Plus size={16} />登记支出</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 12, marginBottom: 18 }}>
        <div className="glass-card" style={{ padding: 18 }}><div className="stat-label">累计垫付</div><div className="stat-value">{money(data?.total_amount ?? 0)}</div></div>
        <div className="glass-card" style={{ padding: 18 }}><div className="stat-label">待报销</div><div className="stat-value" style={{ color: 'var(--color-expense)' }}>{money(data?.total_unreimbursed ?? 0)}</div></div>
      </div>
      <div className="glass-card" style={{ overflowX: 'auto' }}>
        {!data?.items.length ? <div className="empty-state">暂无垫付支出</div> : <table className="data-table">
          <thead><tr><th>日期</th><th>成员</th><th>分类</th><th>金额</th><th>凭证</th><th>状态</th><th></th></tr></thead>
          <tbody>{data.items.map((expense) => <tr key={expense.id}>
            <td>{expense.business_date}</td><td>{expense.member_name}</td><td>{expense.category_name ?? '未分类'}</td>
            <td style={{ fontWeight: 700 }}>{money(expense.amount)}</td>
            <td>{expense.receipt_url ? <a href={expense.receipt_url} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-light)' }}><FileText size={15} /></a> : '—'}</td>
            <td><button className="btn btn-ghost btn-sm" onClick={() => toggle(expense)}><Receipt size={13} />{expense.reimbursed ? '已报销' : '未报销'}</button></td>
            <td><button className="btn btn-danger btn-sm btn-icon" onClick={() => remove(expense)}><Trash2 size={13} /></button></td>
          </tr>)}</tbody>
        </table>}
      </div>
      <AddExpenseModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSuccess={() => { setModalOpen(false); showToast('支出已登记', 'success'); load() }} />
    </>
  )
}
