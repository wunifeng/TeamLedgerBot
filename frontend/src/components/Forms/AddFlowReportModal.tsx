import { useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { Modal } from '@/components/UI/Modal'
import { flowsApi, membersApi, venuesApi } from '@/services/api'
import type { DailyFlowResponse, MemberResponse, VenueResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

interface Props {
  isOpen: boolean
  onClose: () => void
  onSuccess: (flow: DailyFlowResponse) => void
}

const initialForm = () => ({
  business_date: format(new Date(), 'yyyy-MM-dd'),
  member_id: '',
  venue_id: '',
  game: '',
  card_number: '0',
  principal: '',
  chip_code: '',
  loss_rebate: '',
  profit_loss: '',
  remark: '',
})

export function AddFlowReportModal({ isOpen, onClose, onSuccess }: Props) {
  const { showToast } = useApp()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [venues, setVenues] = useState<VenueResponse[]>([])
  const [games, setGames] = useState<string[]>([])
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    setForm(initialForm())
    Promise.all([membersApi.list(), venuesApi.list(), venuesApi.games()]).then(([memberRows, venueRows, gameRows]) => {
      setMembers(memberRows)
      setVenues(venueRows)
      setGames(gameRows)
      setForm((current) => ({
        ...current,
        member_id: memberRows[0]?.id ?? '',
        venue_id: venueRows[0]?.id ?? '',
        game: gameRows[0] ?? '',
      }))
    }).catch((error) => showToast(error.message, 'error'))
  }, [isOpen, showToast])

  const calculatedProfitLoss = useMemo(() => {
    const principal = Number(form.principal || 0)
    const chipCode = Number(form.chip_code || 0)
    const lossRebate = Number(form.loss_rebate || 0)
    return chipCode + lossRebate - principal
  }, [form.principal, form.chip_code, form.loss_rebate])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!form.member_id || !form.venue_id || !form.game) {
      showToast('请先维护成员、场子和游戏配置', 'error')
      return
    }
    setLoading(true)
    try {
      const flow = await flowsApi.create({
        ...form,
        principal: Number(form.principal),
        chip_code: Number(form.chip_code),
        loss_rebate: Number(form.loss_rebate),
        profit_loss: Number(form.profit_loss),
        remark: form.remark || undefined,
      })
      onSuccess(flow)
    } catch (error: any) {
      showToast(error.message ?? '流水提交失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  const field = (name: keyof ReturnType<typeof initialForm>, value: string) =>
    setForm((current) => ({ ...current, [name]: value }))

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="上报每日流水">
      <form onSubmit={submit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div className="form-group">
            <label className="form-label">日期 *</label>
            <input className="form-input" type="date" value={form.business_date} onChange={(e) => field('business_date', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">人员 *</label>
            <select className="form-input" value={form.member_id} onChange={(e) => field('member_id', e.target.value)} required>
              {members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">场子 *</label>
            <select className="form-input" value={form.venue_id} onChange={(e) => field('venue_id', e.target.value)} required>
              {venues.map((venue) => <option key={venue.id} value={venue.id}>{venue.name} · 输返 {venue.rebate_rate}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">游戏 *</label>
            <select className="form-input" value={form.game} onChange={(e) => field('game', e.target.value)} required>
              {games.map((game) => <option key={game} value={game}>{game}</option>)}
            </select>
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">卡号 *</label>
          <input className="form-input" value={form.card_number} onChange={(e) => field('card_number', e.target.value)} placeholder="未看到会员卡号时填写 0" required />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 10 }}>
          <div className="form-group">
            <label className="form-label">本金 *</label>
            <input className="form-input" type="number" min="0" step="0.01" value={form.principal} onChange={(e) => field('principal', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">点码 *</label>
            <input className="form-input" type="number" min="0" step="0.01" value={form.chip_code} onChange={(e) => field('chip_code', e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">输反 *</label>
            <input className="form-input" type="number" min="0" step="0.01" value={form.loss_rebate} onChange={(e) => field('loss_rebate', e.target.value)} required />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">赢亏 * <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>系统复算：{calculatedProfitLoss}</span></label>
          <input className="form-input" type="number" step="0.01" value={form.profit_loss} onChange={(e) => field('profit_loss', e.target.value)} required />
        </div>
        <div className="form-group">
          <label className="form-label">备注</label>
          <input className="form-input" maxLength={500} value={form.remark} onChange={(e) => field('remark', e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={onClose}>取消</button>
          <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={loading}>{loading ? '校验并提交中...' : '校验并提交'}</button>
        </div>
      </form>
    </Modal>
  )
}
