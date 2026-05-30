import { useEffect, useMemo, useState } from 'react'
import { Modal } from '@/components/UI/Modal'
import { flowsApi } from '@/services/api'
import type { DailyFlowResponse, DailyFlowUpdate } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  flow: DailyFlowResponse | null
  onClose: () => void
  onSuccess: (updated: DailyFlowResponse) => void
}

export function EditFlowModal({ isOpen, flow, onClose, onSuccess }: Props) {
  const { showToast } = useApp()
  const [form, setForm] = useState({ principal: '', chip_code: '', loss_rebate: '', profit_loss: '', remark: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen && flow) {
      setForm({
        principal: String(flow.principal),
        chip_code: String(flow.chip_code),
        loss_rebate: String(flow.loss_rebate),
        profit_loss: String(flow.profit_loss),
        remark: flow.remark ?? '',
      })
    }
  }, [isOpen, flow])

  const calculatedProfitLoss = useMemo(() => {
    const p = Number(form.principal || 0)
    const c = Number(form.chip_code || 0)
    const l = Number(form.loss_rebate || 0)
    return Number((c + l - p).toFixed(2))
  }, [form.principal, form.chip_code, form.loss_rebate])

  const field = (name: keyof typeof form, value: string) =>
    setForm((cur) => ({ ...cur, [name]: value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!flow) return
    setLoading(true)
    try {
      const payload: DailyFlowUpdate = {
        principal: Number(form.principal),
        chip_code: Number(form.chip_code),
        loss_rebate: Number(form.loss_rebate),
        profit_loss: Number(form.profit_loss),
        remark: form.remark || undefined,
      }
      const updated = await flowsApi.patch(flow.id, payload)
      onSuccess(updated)
    } catch (err: any) {
      showToast(err.message ?? '修改失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!flow) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`编辑流水 — ${flow.member_name} · ${flow.business_date}`}>
      <form onSubmit={submit}>
        {/* 只读展示 */}
        <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: 'var(--text-muted)' }}>
          <strong style={{ color: 'var(--text-primary)' }}>{flow.venue_name}</strong> · {flow.game} · 卡号 {flow.card_number}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 10 }}>
          <div className="form-group">
            <label className="form-label">本金 *</label>
            <input id="edit-flow-principal" className="form-input" type="number" min="0" step="0.01"
              value={form.principal} onChange={(e) => field('principal', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">点码 *</label>
            <input id="edit-flow-chip-code" className="form-input" type="number" min="0" step="0.01"
              value={form.chip_code} onChange={(e) => field('chip_code', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">输反 *</label>
            <input id="edit-flow-loss-rebate" className="form-input" type="number" min="0" step="0.01"
              value={form.loss_rebate} onChange={(e) => field('loss_rebate', e.target.value)} required />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">
            赢亏 * <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>系统复算：{calculatedProfitLoss}</span>
          </label>
          <input id="edit-flow-profit-loss" className="form-input" type="number" step="0.01"
            value={form.profit_loss} onChange={(e) => field('profit_loss', e.target.value)} required />
        </div>

        <div className="form-group">
          <label className="form-label">备注</label>
          <input id="edit-flow-remark" className="form-input" maxLength={500}
            value={form.remark} onChange={(e) => field('remark', e.target.value)} />
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
