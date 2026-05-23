import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts'
import { TrendingUp, TrendingDown, Wallet, DollarSign, Plus } from 'lucide-react'
import { dashboardApi } from '@/services/api'
import type { SummaryResponse, MonthlyTrendItem, CategoryBreakdownItem } from '@/types/api'
import { useApp } from '@/context/AppContext'
import { AddTransactionModal } from '@/components/Forms/AddTransactionModal'

const PIE_COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#06b6d4', '#84cc16']

function fmt(val: number) {
  return new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(val)
}

interface KpiCardProps {
  label: string
  value: number
  icon: React.ReactNode
  variant: 'income' | 'expense' | 'salary' | 'profit'
  delay?: number
}

function KpiCard({ label, value, icon, variant, delay = 0 }: KpiCardProps) {
  const colors = {
    income: 'var(--color-income)',
    expense: 'var(--color-expense)',
    salary: 'var(--color-salary)',
    profit: value >= 0 ? 'var(--color-income)' : 'var(--color-expense)',
  }
  return (
    <motion.div
      className={`glass-card kpi-card kpi-${variant}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4, ease: 'easeOut' }}
      style={{ padding: '20px 24px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span className="stat-label">{label}</span>
        <div
          style={{
            color: colors[variant],
            opacity: 0.8,
            background: `${colors[variant]}18`,
            padding: 8,
            borderRadius: 8,
          }}
        >
          {icon}
        </div>
      </div>
      <div className="stat-value" style={{ color: colors[variant] }}>
        ¥{fmt(value)}
      </div>
    </motion.div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card-sm" style={{ padding: '10px 14px', fontSize: 13 }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 6 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color, marginBottom: 2 }}>
          {p.name}: ¥{fmt(p.value)}
        </p>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const { showToast } = useApp()
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [trend, setTrend] = useState<MonthlyTrendItem[]>([])
  const [breakdown, setBreakdown] = useState<CategoryBreakdownItem[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)

  const loadData = useCallback(async () => {
    try {
      const [sum, tr, bd] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getMonthlyTrend(6),
        dashboardApi.getCategoryBreakdown(),
      ])
      setSummary(sum)
      setTrend(tr.data)
      setBreakdown(bd.expense)
    } catch (e: any) {
      showToast(e.message ?? '加载数据失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => { loadData() }, [loadData])

  return (
    <>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <h1 className="page-title">财务仪表盘</h1>
            <p className="page-subtitle">实时收支总览与趋势分析</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="btn btn-primary"
            onClick={() => setModalOpen(true)}
          >
            <Plus size={16} />
            新增交易
          </motion.button>
        </div>
      </div>

      {/* KPI Cards */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 28 }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 110, borderRadius: 16 }} />
          ))}
        </div>
      ) : summary ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 28 }}>
          <KpiCard label="总收入" value={summary.total_income} icon={<TrendingUp size={18} />} variant="income" delay={0} />
          <KpiCard label="总支出" value={summary.total_expense} icon={<TrendingDown size={18} />} variant="expense" delay={0.07} />
          <KpiCard label="薪资发放" value={summary.total_salary} icon={<Wallet size={18} />} variant="salary" delay={0.14} />
          <KpiCard label="净利润" value={summary.net_profit} icon={<DollarSign size={18} />} variant="profit" delay={0.21} />
        </div>
      ) : null}

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,2fr) minmax(0,1fr)', gap: 20, marginBottom: 24 }}>
        {/* Area chart */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.28 }}
          style={{ padding: '20px 24px' }}
        >
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 20, color: 'var(--text-primary)' }}>近 6 个月收支趋势</h3>
          {loading ? (
            <div className="skeleton" style={{ height: 220 }} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradExpense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="income" name="收入" stroke="#10b981" strokeWidth={2} fill="url(#gradIncome)" dot={false} />
                <Area type="monotone" dataKey="expense" name="支出" stroke="#f43f5e" strokeWidth={2} fill="url(#gradExpense)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* Donut chart */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          style={{ padding: '20px 24px' }}
        >
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 20, color: 'var(--text-primary)' }}>支出分类占比</h3>
          {loading ? (
            <div className="skeleton" style={{ height: 220 }} />
          ) : breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={breakdown}
                  dataKey="total"
                  nameKey="category_name"
                  cx="50%"
                  cy="50%"
                  innerRadius="55%"
                  outerRadius="80%"
                  paddingAngle={3}
                >
                  {breakdown.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend
                  formatter={(value) => (
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{value}</span>
                  )}
                />
                <Tooltip
                  formatter={(val) => [`¥${fmt(Number(val ?? 0))}`, '金额']}
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ height: 220 }}>暂无分类数据</div>
          )}
        </motion.div>
      </div>

      <AddTransactionModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => { setModalOpen(false); loadData(); showToast('记账成功！', 'success') }}
      />
    </>
  )
}
