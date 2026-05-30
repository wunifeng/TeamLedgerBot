import { useCallback, useEffect, useState } from 'react'
import { Pencil, Plus, Tag, Trash2 } from 'lucide-react'
import { Modal } from '@/components/UI/Modal'
import { categoriesApi, venuesApi } from '@/services/api'
import type { CategoryResponse, VenueResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

export default function SettingsPage() {
  const { showToast } = useApp()
  const [venues, setVenues] = useState<VenueResponse[]>([])
  const [categories, setCategories] = useState<CategoryResponse[]>([])
  const [rates, setRates] = useState<number[]>([])
  const [venueModal, setVenueModal] = useState(false)
  const [venueTarget, setVenueTarget] = useState<VenueResponse | null>(null)
  const [venueName, setVenueName] = useState('')
  const [rate, setRate] = useState('0.2')
  const [categoryName, setCategoryName] = useState('')

  const load = useCallback(async () => {
    try {
      const [venueRows, categoryRows, rateRows] = await Promise.all([venuesApi.list(true), categoriesApi.listExpenses(), venuesApi.rebateRates()])
      setVenues(venueRows); setCategories(categoryRows); setRates(rateRows)
      if (rateRows.length && !rateRows.includes(Number(rate))) setRate(String(rateRows[0]))
    } catch (error: any) { showToast(error.message, 'error') }
  }, [rate, showToast])
  useEffect(() => { load() }, [load])

  const openVenue = (venue?: VenueResponse) => {
    setVenueTarget(venue ?? null); setVenueName(venue?.name ?? ''); setRate(String(venue?.rebate_rate ?? rates[0] ?? 0.2)); setVenueModal(true)
  }
  const saveVenue = async (event: React.FormEvent) => {
    event.preventDefault()
    try {
      if (venueTarget) await venuesApi.update(venueTarget.id, { name: venueName, rebate_rate: Number(rate) })
      else await venuesApi.create({ name: venueName, rebate_rate: Number(rate) })
      setVenueModal(false); showToast('场子配置已保存', 'success'); load()
    } catch (error: any) { showToast(error.message, 'error') }
  }
  const toggleVenue = async (venue: VenueResponse) => {
    try { await venuesApi.update(venue.id, { is_active: !venue.is_active }); load() } catch (error: any) { showToast(error.message, 'error') }
  }
  const addCategory = async (event: React.FormEvent) => {
    event.preventDefault()
    try { await categoriesApi.createExpense({ name: categoryName }); setCategoryName(''); load() } catch (error: any) { showToast(error.message, 'error') }
  }

  return (
    <>
      <div style={{ marginBottom: 24 }}><h1 className="page-title">业务设置</h1><p className="page-subtitle">维护固定场子、输返比例和成员垫付分类</p></div>
      <section className="glass-card" style={{ padding: 20, marginBottom: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}><div><h3>场子配置</h3><p style={{ color: 'var(--text-muted)', fontSize: 12 }}>输返比例决定每日流水采用哪组工资规则</p></div><button className="btn btn-primary btn-sm" onClick={() => openVenue()}><Plus size={14} />新增场子</button></div>
        {!venues.length ? <div className="empty-state">尚未维护场子</div> : <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 10 }}>{venues.map((venue) => <div key={venue.id} style={{ border: '1px solid var(--border-subtle)', borderRadius: 12, padding: 14, background: 'rgba(255,255,255,.025)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}><strong>{venue.name}</strong><span className="badge">{venue.is_active ? '启用' : '停用'}</span></div>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, margin: '8px 0 12px' }}>输返比例：{venue.rebate_rate}</div>
          <div style={{ display: 'flex', gap: 8 }}><button className="btn btn-ghost btn-sm" onClick={() => openVenue(venue)}><Pencil size={13} />更新</button><button className="btn btn-ghost btn-sm" onClick={() => toggleVenue(venue)}>{venue.is_active ? '停用' : '启用'}</button></div>
        </div>)}</div>}
      </section>
      <section className="glass-card" style={{ padding: 20 }}>
        <div style={{ marginBottom: 14 }}><h3>垫付分类</h3><p style={{ color: 'var(--text-muted)', fontSize: 12 }}>例如差旅费、餐饮费、采购费</p></div>
        <form onSubmit={addCategory} style={{ display: 'flex', gap: 8, marginBottom: 14 }}><input className="form-input" value={categoryName} onChange={(e) => setCategoryName(e.target.value)} placeholder="新增分类名称" required /><button className="btn btn-primary" type="submit"><Plus size={14} />新增</button></form>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>{categories.map((category) => <div key={category.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', border: '1px solid var(--border-subtle)', borderRadius: 9 }}><Tag size={13} />{category.name}<button className="btn btn-danger btn-sm btn-icon" onClick={() => categoriesApi.delete(category.id).then(load)}><Trash2 size={11} /></button></div>)}</div>
      </section>
      <Modal isOpen={venueModal} onClose={() => setVenueModal(false)} title={venueTarget ? '更新场子' : '新增场子'}><form onSubmit={saveVenue}><div className="form-group"><label className="form-label">场子名称 *</label><input className="form-input" value={venueName} onChange={(e) => setVenueName(e.target.value)} required /></div><div className="form-group"><label className="form-label">输返比例 *</label><select className="form-input" value={rate} onChange={(e) => setRate(e.target.value)}>{rates.map((item) => <option key={item} value={item}>{item}</option>)}</select></div><button className="btn btn-primary" type="submit">保存场子</button></form></Modal>
    </>
  )
}
