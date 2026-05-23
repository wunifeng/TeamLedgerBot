import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Plus, Trash2, Tag } from 'lucide-react'
import { categoriesApi } from '@/services/api'
import type { CategoryResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'
import { Modal } from '@/components/UI/Modal'

const TYPE_COLORS = {
  income: 'var(--color-income)',
  expense: 'var(--color-expense)',
}

export default function SettingsPage() {
  const { showToast } = useApp()
  const [categories, setCategories] = useState<CategoryResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [tabFilter, setTabFilter] = useState<'income' | 'expense' | ''>('')

  // New category form
  const [name, setName] = useState('')
  const [type, setType] = useState<'income' | 'expense'>('expense')
  const [desc, setDesc] = useState('')
  const [saving, setSaving] = useState(false)

  const loadCategories = useCallback(async () => {
    setLoading(true)
    try {
      setCategories(await categoriesApi.list({ type: tabFilter || undefined }))
    } catch (e: any) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [tabFilter, showToast])

  useEffect(() => { loadCategories() }, [loadCategories])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    try {
      await categoriesApi.create({ name: name.trim(), type, description: desc.trim() || undefined })
      showToast(`分类「${name}」已创建`, 'success')
      setName(''); setDesc(''); setModalOpen(false)
      loadCategories()
    } catch (err: any) {
      showToast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (cat: CategoryResponse) => {
    if (!confirm(`确定要停用分类「${cat.name}」吗？`)) return
    try {
      await categoriesApi.delete(cat.id)
      showToast(`分类「${cat.name}」已停用`, 'success')
      loadCategories()
    } catch (e: any) {
      showToast(e.message, 'error')
    }
  }

  const income = categories.filter((c) => c.type === 'income')
  const expense = categories.filter((c) => c.type === 'expense')

  const CategorySection = ({ title, items, color }: { title: string; items: CategoryResponse[]; color: string }) => (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Tag size={14} style={{ color }} />
        <span style={{ fontSize: 13, fontWeight: 600, color }}>{title}</span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 4 }}>({items.length})</span>
      </div>
      {items.length === 0 ? (
        <p style={{ fontSize: 13, color: 'var(--text-muted)', paddingLeft: 22 }}>暂无分类</p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {items.map((cat, i) => (
            <motion.div
              key={cat.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '7px 12px',
                background: `${color}12`,
                border: `1px solid ${color}28`,
                borderRadius: 10,
                fontSize: 13,
                color: 'var(--text-primary)',
              }}
            >
              <span>{cat.name}</span>
              {cat.description && (
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>· {cat.description}</span>
              )}
              <button
                className="btn btn-danger btn-sm btn-icon"
                style={{ padding: '2px', marginLeft: 2 }}
                onClick={() => handleDelete(cat)}
                title="停用分类"
              >
                <Trash2 size={11} />
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <h1 className="page-title">分类设置</h1>
            <p className="page-subtitle">管理收入与支出的分类标签</p>
          </div>
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={16} />新增分类
          </button>
        </div>
      </div>

      <motion.div className="glass-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '24px' }}>
        {loading ? (
          <div>
            {[...Array(6)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 36, marginBottom: 8, borderRadius: 10 }} />
            ))}
          </div>
        ) : (
          <>
            <CategorySection title="收入分类" items={income} color="var(--color-income)" />
            <hr className="divider" />
            <CategorySection title="支出分类" items={expense} color="var(--color-expense)" />
          </>
        )}
      </motion.div>

      {/* Create modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="新增分类">
        <form onSubmit={handleCreate}>
          <div className="form-group">
            <label className="form-label">类型</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {(['income', 'expense'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  style={{
                    flex: 1, padding: '8px', borderRadius: 8, border: '1px solid',
                    borderColor: type === t ? TYPE_COLORS[t] + '60' : 'var(--border-default)',
                    background: type === t ? TYPE_COLORS[t] + '15' : 'transparent',
                    color: type === t ? TYPE_COLORS[t] : 'var(--text-muted)',
                    fontSize: 13, fontWeight: type === t ? 600 : 400, cursor: 'pointer', fontFamily: 'inherit',
                  }}
                >
                  {t === 'income' ? '💰 收入' : '💸 支出'}
                </button>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">分类名称 *</label>
            <input
              className="form-input"
              type="text"
              placeholder="例：服务器、餐饮、广告"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">描述（可选）</label>
            <input
              className="form-input"
              type="text"
              placeholder="简短说明"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setModalOpen(false)}>取消</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={saving}>
              {saving ? '创建中...' : '确认创建'}
            </button>
          </div>
        </form>
      </Modal>
    </>
  )
}
