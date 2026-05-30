import { useEffect, useState } from 'react'
import { Clock, Plus, Edit2, Trash2, Loader } from 'lucide-react'
import { Modal } from '@/components/UI/Modal'
import { expensesApi } from '@/services/api'
import type { ExpenseChangeLogResponse, MemberExpenseResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  expense: MemberExpenseResponse | null
  onClose: () => void
}

const CHANGE_TYPE_CONFIG = {
  create: { label: '创建', icon: Plus, color: 'var(--color-income)' },
  update: { label: '修改', icon: Edit2, color: 'var(--color-accent)' },
  delete: { label: '删除', icon: Trash2, color: 'var(--color-expense)' },
}

const FIELD_LABELS: Record<string, string> = {
  amount: '金额',
  category_name: '分类',
  remark: '备注',
}

function formatDatetime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

export function ExpenseHistoryModal({ isOpen, expense, onClose }: Props) {
  const { showToast } = useApp()
  const [logs, setLogs] = useState<ExpenseChangeLogResponse[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen || !expense) return
    setLoading(true)
    expensesApi.history(expense.id)
      .then(setLogs)
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [isOpen, expense, showToast])

  if (!expense) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`变更历史 — ${expense.member_name} · ${expense.business_date}`}>
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', padding: 24 }}>
          <Loader size={16} /> 加载中...
        </div>
      ) : logs.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', padding: 24, textAlign: 'center' }}>暂无变更记录</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {logs.map((log, idx) => {
            const cfg = CHANGE_TYPE_CONFIG[log.change_type as keyof typeof CHANGE_TYPE_CONFIG] ?? CHANGE_TYPE_CONFIG.update
            const Icon = cfg.icon
            return (
              <div key={log.id} style={{
                display: 'flex', gap: 12,
                paddingBottom: idx < logs.length - 1 ? 12 : 0,
                borderBottom: idx < logs.length - 1 ? '1px solid var(--border-color)' : 'none',
              }}>
                <div style={{ flexShrink: 0, paddingTop: 2 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: '50%',
                    background: cfg.color + '22',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    border: `1.5px solid ${cfg.color}55`,
                  }}>
                    <Icon size={13} color={cfg.color} />
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{
                      fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10,
                      background: cfg.color + '20', color: cfg.color,
                    }}>{cfg.label}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Clock size={11} /> {formatDatetime(log.changed_at)}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>
                      {log.operator_name}
                    </span>
                  </div>
                  {log.change_type === 'update' && log.before_data && log.after_data && (
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 6, padding: '8px 12px' }}>
                      {Object.keys(FIELD_LABELS).map((key) => {
                        const before = log.before_data?.[key] ?? null
                        const after = log.after_data?.[key] ?? null
                        if (before === null && after === null) return null
                        const changed = before !== after
                        return (
                          <div key={key} style={{
                            display: 'flex', gap: 8, alignItems: 'baseline', fontSize: 13, padding: '3px 0',
                            color: changed ? 'var(--text-primary)' : 'var(--text-muted)',
                          }}>
                            <span style={{ minWidth: 36, color: 'var(--text-muted)' }}>{FIELD_LABELS[key]}</span>
                            {changed ? (
                              <>
                                <span style={{ textDecoration: 'line-through', color: 'var(--color-expense)', opacity: 0.8 }}>{before ?? '—'}</span>
                                <span style={{ color: 'var(--text-muted)' }}>→</span>
                                <span style={{ color: 'var(--color-income)', fontWeight: 600 }}>{after ?? '—'}</span>
                              </>
                            ) : <span>{after ?? '—'}</span>}
                          </div>
                        )
                      })}
                    </div>
                  )}
                  {log.change_type === 'create' && log.after_data && (
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 6, padding: '8px 12px', fontSize: 13 }}>
                      <span style={{ color: 'var(--text-muted)' }}>金额：</span>
                      <span style={{ color: 'var(--color-income)', fontWeight: 600 }}>{log.after_data.amount}</span>
                      {log.after_data.category_name && (
                        <span style={{ color: 'var(--text-muted)', marginLeft: 12 }}>分类：{log.after_data.category_name}</span>
                      )}
                    </div>
                  )}
                  {log.change_type === 'delete' && log.before_data && (
                    <div style={{ background: 'var(--color-expense)10', borderRadius: 6, padding: '8px 12px', fontSize: 13, color: 'var(--text-muted)' }}>
                      金额：{log.before_data.amount}，分类：{log.before_data.category_name ?? '未分类'}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Modal>
  )
}
