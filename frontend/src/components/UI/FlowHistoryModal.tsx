import { useEffect, useState } from 'react'
import { Clock, Plus, Edit2, Trash2, Loader } from 'lucide-react'
import { Modal } from '@/components/UI/Modal'
import { flowsApi } from '@/services/api'
import type { DailyFlowResponse, FlowChangeLogResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  flow: DailyFlowResponse | null
  onClose: () => void
}

const CHANGE_TYPE_CONFIG = {
  create: { label: '创建', icon: Plus, color: 'var(--color-income)' },
  update: { label: '修改', icon: Edit2, color: 'var(--color-accent)' },
  delete: { label: '删除', icon: Trash2, color: 'var(--color-expense)' },
}

const FIELD_LABELS: Record<string, string> = {
  principal: '本金',
  chip_code: '点码',
  loss_rebate: '输反',
  profit_loss: '赢亏',
  remark: '备注',
  salary_amount: '工资',
}

function formatDatetime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function DiffRow({ label, before, after }: { label: string; before: string | null; after: string | null }) {
  const changed = before !== after
  return (
    <div style={{
      display: 'flex', gap: 8, alignItems: 'baseline', fontSize: 13,
      padding: '4px 0',
      color: changed ? 'var(--text-primary)' : 'var(--text-muted)',
    }}>
      <span style={{ minWidth: 42, color: 'var(--text-muted)' }}>{label}</span>
      {changed ? (
        <>
          <span style={{ textDecoration: 'line-through', color: 'var(--color-expense)', opacity: 0.8 }}>{before ?? '—'}</span>
          <span style={{ color: 'var(--text-muted)' }}>→</span>
          <span style={{ color: 'var(--color-income)', fontWeight: 600 }}>{after ?? '—'}</span>
        </>
      ) : (
        <span>{after ?? '—'}</span>
      )}
    </div>
  )
}

export function FlowHistoryModal({ isOpen, flow, onClose }: Props) {
  const { showToast } = useApp()
  const [logs, setLogs] = useState<FlowChangeLogResponse[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen || !flow) return
    setLoading(true)
    flowsApi.history(flow.id)
      .then(setLogs)
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [isOpen, flow, showToast])

  if (!flow) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`变更历史 — ${flow.member_name} · ${flow.business_date}`}>
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', padding: 24 }}>
          <Loader size={16} className="spin" /> 加载中...
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
                {/* 时间线节点 */}
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

                {/* 内容 */}
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

                  {/* 字段差异 */}
                  {log.change_type === 'update' && log.before_data && log.after_data && (
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 6, padding: '8px 12px' }}>
                      {Object.keys(FIELD_LABELS).map((key) => {
                        const before = log.before_data?.[key] ?? null
                        const after = log.after_data?.[key] ?? null
                        if (before === null && after === null) return null
                        return <DiffRow key={key} label={FIELD_LABELS[key]} before={before} after={after} />
                      })}
                    </div>
                  )}
                  {log.change_type === 'create' && log.after_data && (
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 6, padding: '8px 12px' }}>
                      {Object.entries(log.after_data).filter(([, v]) => v != null).map(([key, val]) => (
                        <div key={key} style={{ fontSize: 13, color: 'var(--text-muted)', padding: '2px 0' }}>
                          <span style={{ minWidth: 42, display: 'inline-block' }}>{FIELD_LABELS[key] ?? key}</span>
                          <span style={{ color: 'var(--text-primary)' }}>{val}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {log.change_type === 'delete' && log.before_data && (
                    <div style={{ background: 'var(--color-expense)10', borderRadius: 6, padding: '8px 12px', fontSize: 13, color: 'var(--text-muted)' }}>
                      赢亏：{log.before_data.profit_loss}，工资：{log.before_data.salary_amount}
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
