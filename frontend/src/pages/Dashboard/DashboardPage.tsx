import { useCallback, useEffect, useState } from 'react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Landmark, Plus, ReceiptText, Wallet, Waves } from 'lucide-react'
import { AddFlowReportModal } from '@/components/Forms/AddFlowReportModal'
import { dashboardApi } from '@/services/api'
import type { DailyTrendItem, SummaryResponse, VenueBreakdownResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

function money(value: number) {
  return `¥${new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(value || 0)}`
}

export default function DashboardPage() {
  const { showToast } = useApp()
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [trend, setTrend] = useState<DailyTrendItem[]>([])
  const [venues, setVenues] = useState<VenueBreakdownResponse['items']>([])
  const [modalOpen, setModalOpen] = useState(false)

  const load = useCallback(async () => {
    try {
      const [nextSummary, nextTrend, nextVenues] = await Promise.all([
        dashboardApi.getSummary(), dashboardApi.getDailyTrend(30), dashboardApi.getVenueBreakdown(),
      ])
      setSummary(nextSummary); setTrend(nextTrend.data); setVenues(nextVenues.items)
    } catch (error: any) { showToast(error.message, 'error') }
  }, [showToast])
  useEffect(() => { load() }, [load])

  const cards = [
    { label: '业务赢亏', value: summary?.total_profit_loss ?? 0, icon: Waves, color: 'var(--color-income)' },
    { label: '成员垫付', value: summary?.total_expense ?? 0, icon: ReceiptText, color: 'var(--color-expense)' },
    { label: '自动计提工资', value: summary?.total_salary ?? 0, icon: Wallet, color: 'var(--color-salary)' },
    { label: '净结果', value: summary?.net_result ?? 0, icon: Landmark, color: (summary?.net_result ?? 0) >= 0 ? 'var(--color-income)' : 'var(--color-expense)' },
  ]

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div><h1 className="page-title">业务总览</h1><p className="page-subtitle">每日流水、成员垫付与工资计提集中视图</p></div>
        <button className="btn btn-primary" onClick={() => setModalOpen(true)}><Plus size={16} />上报流水</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))', gap: 14, marginBottom: 20 }}>
        {cards.map(({ label, value, icon: Icon, color }) => <div className="glass-card" style={{ padding: 18 }} key={label}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: 10 }}><span className="stat-label">{label}</span><Icon size={16} style={{ color }} /></div>
          <div className="stat-value" style={{ color }}>{money(value)}</div>
        </div>)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
        <div className="glass-card" style={{ padding: 18 }}>
          <h3 style={{ marginBottom: 16 }}>近 30 天业务趋势</h3>
          <ResponsiveContainer width="100%" height={260}><AreaChart data={trend}>
            <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} /><YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,.12)' }} />
            <Area type="monotone" dataKey="profit_loss" name="赢亏" stroke="#10b981" fill="rgba(16,185,129,.18)" />
            <Area type="monotone" dataKey="net" name="净结果" stroke="#6366f1" fill="rgba(99,102,241,.1)" />
          </AreaChart></ResponsiveContainer>
        </div>
        <div className="glass-card" style={{ padding: 18 }}>
          <h3 style={{ marginBottom: 16 }}>场子表现</h3>
          {!venues.length ? <div className="empty-state">暂无数据</div> : venues.map((venue) => <div key={venue.venue_name} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: '11px 0', borderBottom: '1px solid var(--border-subtle)' }}>
            <div><strong>{venue.venue_name}</strong><div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{venue.flow_count} 条流水</div></div>
            <span style={{ color: venue.profit_loss >= 0 ? 'var(--color-income)' : 'var(--color-expense)', fontWeight: 700 }}>{money(venue.profit_loss)}</span>
          </div>)}
        </div>
      </div>
      <AddFlowReportModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSuccess={(flow) => { setModalOpen(false); showToast(`流水已提交，工资 ¥${flow.salary_amount}`, 'success'); load() }} />
    </>
  )
}
