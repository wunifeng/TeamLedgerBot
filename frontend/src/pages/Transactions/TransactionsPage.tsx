import { useCallback, useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, History, Pencil, Plus, Trash2 } from 'lucide-react'
import { flowsApi } from '@/services/api'
import type { DailyFlowListResponse, DailyFlowResponse } from '@/types/api'
import { AddFlowReportModal } from '@/components/Forms/AddFlowReportModal'
import { EditFlowModal } from '@/components/Forms/EditFlowModal'
import { FlowHistoryModal } from '@/components/UI/FlowHistoryModal'
import { useApp } from '@/context/AppContext'

function money(value: number) {
  return new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2 }).format(value)
}

export default function TransactionsPage() {
  const { showToast, currentMember } = useApp()
  const [data, setData] = useState<DailyFlowListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [addOpen, setAddOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<DailyFlowResponse | null>(null)
  const [historyTarget, setHistoryTarget] = useState<DailyFlowResponse | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setData(await flowsApi.list({ page, limit: 15 }))
    } catch (error: any) {
      showToast(error.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [page, showToast])

  useEffect(() => { load() }, [load])

  const canEdit = (flow: DailyFlowResponse) =>
    !!(currentMember?.is_admin || currentMember?.id === flow.member_id)

  const remove = async (flow: DailyFlowResponse) => {
    if (!confirm(`确定删除 ${flow.member_name} 在 ${flow.business_date} 的流水吗？`)) return
    try {
      await flowsApi.delete(flow.id)
      showToast('流水已删除，月度工资会自动重算', 'success')
      load()
    } catch (error: any) {
      showToast(error.message, 'error')
    }
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div>
          <h1 className="page-title">每日流水</h1>
          <p className="page-subtitle">按场子和游戏记录业务结果，系统同步校验赢亏并计算工资</p>
        </div>
        <button className="btn btn-primary" onClick={() => setAddOpen(true)}>
          <Plus size={16} />上报流水
        </button>
      </div>

      <div className="glass-card" style={{ overflowX: 'auto' }}>
        {loading ? (
          <div className="empty-state">正在加载...</div>
        ) : !data?.items.length ? (
          <div className="empty-state">暂无流水记录</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>日期</th><th>成员</th><th>场子 / 游戏</th>
                <th>本金</th><th>点码</th><th>输反</th><th>赢亏</th><th>工资</th><th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((flow) => (
                <tr key={flow.id}>
                  <td>{flow.business_date}</td>
                  <td>{flow.member_name}</td>
                  <td>
                    <strong>{flow.venue_name}</strong>
                    <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{flow.game} · 卡号 {flow.card_number}</div>
                  </td>
                  <td>¥{money(flow.principal)}</td>
                  <td>¥{money(flow.chip_code)}</td>
                  <td>¥{money(flow.loss_rebate)}</td>
                  <td style={{
                    color: flow.profit_loss >= 0 ? 'var(--color-income)' : 'var(--color-expense)',
                    fontWeight: 700,
                  }}>
                    {flow.profit_loss >= 0 ? '+' : ''}¥{money(flow.profit_loss)}
                  </td>
                  <td><span className="badge badge-salary">¥{money(flow.salary_amount)}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {/* 历史按钮（所有登录成员都能查看） */}
                      <button
                        className="btn btn-ghost btn-sm btn-icon"
                        onClick={() => setHistoryTarget(flow)}
                        title="变更历史"
                      >
                        <History size={13} />
                      </button>
                      {/* 编辑按钮（权限控制） */}
                      {canEdit(flow) && (
                        <button
                          className="btn btn-ghost btn-sm btn-icon"
                          onClick={() => setEditTarget(flow)}
                          title="编辑"
                        >
                          <Pencil size={13} />
                        </button>
                      )}
                      {/* 删除按钮（权限控制） */}
                      {canEdit(flow) && (
                        <button
                          className="btn btn-danger btn-sm btn-icon"
                          onClick={() => remove(flow)}
                          title="删除"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.pages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 16 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setPage((v) => Math.max(1, v - 1))} disabled={page === 1}>
            <ChevronLeft size={14} />
          </button>
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{page} / {data.pages}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setPage((v) => Math.min(data.pages, v + 1))} disabled={page === data.pages}>
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      <AddFlowReportModal
        isOpen={addOpen}
        onClose={() => setAddOpen(false)}
        onSuccess={(flow) => { setAddOpen(false); showToast(`流水已提交，工资 ¥${flow.salary_amount}`, 'success'); load() }}
      />

      <EditFlowModal
        isOpen={!!editTarget}
        flow={editTarget}
        onClose={() => setEditTarget(null)}
        onSuccess={(updated) => {
          setEditTarget(null)
          showToast(`流水已修改，新工资 ¥${updated.salary_amount}`, 'success')
          load()
        }}
      />

      <FlowHistoryModal
        isOpen={!!historyTarget}
        flow={historyTarget}
        onClose={() => setHistoryTarget(null)}
      />
    </>
  )
}
