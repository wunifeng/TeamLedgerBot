import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Filter, Trash2, Plus, ChevronLeft, ChevronRight } from 'lucide-react'
import { format } from 'date-fns'
import { transactionsApi, membersApi } from '@/services/api'
import type { TransactionResponse, TransactionListResponse, MemberResponse, TransactionType } from '@/types/api'
import { useApp } from '@/context/AppContext'
import { AddTransactionModal } from '@/components/Forms/AddTransactionModal'

function fmt(val: number) {
  return new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2 }).format(val)
}

const TYPE_MAP: Record<TransactionType, { label: string; cls: string }> = {
  income:  { label: '收入', cls: 'badge-income' },
  expense: { label: '支出', cls: 'badge-expense' },
  salary:  { label: '薪资', cls: 'badge-salary' },
}

export default function TransactionsPage() {
  const { showToast } = useApp()
  const [data, setData] = useState<TransactionListResponse | null>(null)
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Filters
  const [typeFilter, setTypeFilter] = useState<TransactionType | ''>('')
  const [memberFilter, setMemberFilter] = useState('')
  const [page, setPage] = useState(1)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [txRes, mRes] = await Promise.all([
        transactionsApi.list({
          type: typeFilter || undefined,
          member_id: memberFilter || undefined,
          page,
          limit: 15,
        }),
        members.length ? Promise.resolve(members) : membersApi.list(),
      ])
      setData(txRes)
      if (!members.length) setMembers(mRes as MemberResponse[])
    } catch (e: any) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [typeFilter, memberFilter, page, showToast]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { loadData() }, [loadData])

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这条记录吗？')) return
    setDeletingId(id)
    try {
      await transactionsApi.delete(id)
      showToast('记录已删除', 'success')
      loadData()
    } catch (e: any) {
      showToast(e.message, 'error')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <h1 className="page-title">交易流水</h1>
            <p className="page-subtitle">查看和管理所有收支记录</p>
          </div>
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={16} />新增交易
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: 13 }}>
            <Filter size={14} />筛选:
          </div>
          <select
            className="form-input"
            style={{ width: 'auto', padding: '7px 12px', fontSize: 13 }}
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value as TransactionType | ''); setPage(1) }}
          >
            <option value="">全部类型</option>
            <option value="income">收入</option>
            <option value="expense">支出</option>
            <option value="salary">薪资</option>
          </select>
          <select
            className="form-input"
            style={{ width: 'auto', padding: '7px 12px', fontSize: 13 }}
            value={memberFilter}
            onChange={(e) => { setMemberFilter(e.target.value); setPage(1) }}
          >
            <option value="">全部成员</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <motion.div className="glass-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {loading ? (
          <div style={{ padding: 32 }}>
            {[...Array(8)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 44, marginBottom: 8, borderRadius: 8 }} />
            ))}
          </div>
        ) : !data?.items.length ? (
          <div className="empty-state">暂无交易记录</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>类型</th>
                  <th>金额</th>
                  <th>成员</th>
                  <th>分类</th>
                  <th>备注</th>
                  <th>时间</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {data.items.map((tx: TransactionResponse, i) => (
                    <motion.tr
                      key={tx.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.025 }}
                    >
                      <td>
                        <span className={`badge ${TYPE_MAP[tx.type].cls}`}>
                          {TYPE_MAP[tx.type].label}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          fontWeight: 600,
                          fontVariantNumeric: 'tabular-nums',
                          color: tx.type === 'income' ? 'var(--color-income)'
                            : tx.type === 'expense' ? 'var(--color-expense)'
                            : 'var(--color-salary)',
                        }}>
                          ¥{fmt(tx.amount)}
                          {tx.bonus ? <span style={{ fontSize: 11, opacity: 0.7 }}> +{fmt(tx.bonus)}</span> : null}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{tx.member_name}</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>{tx.category_name ?? '—'}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 160 }}>
                        <span className="truncate-1">{tx.remark ?? '—'}</span>
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 12, whiteSpace: 'nowrap' }}>
                        {format(new Date(tx.created_at), 'MM-dd HH:mm')}
                      </td>
                      <td>
                        <button
                          className="btn btn-danger btn-sm btn-icon"
                          onClick={() => handleDelete(tx.id)}
                          disabled={deletingId === tx.id}
                          title="删除"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
              <ChevronLeft size={14} />
            </button>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              {page} / {data.pages}（共 {data.total} 条）
            </span>
            <button className="btn btn-ghost btn-sm" onClick={() => setPage((p) => Math.min(data.pages, p + 1))} disabled={page === data.pages}>
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </motion.div>

      <AddTransactionModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => { setModalOpen(false); loadData(); showToast('记账成功！', 'success') }}
      />
    </>
  )
}
