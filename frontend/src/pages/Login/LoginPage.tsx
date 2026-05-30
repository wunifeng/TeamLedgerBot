import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, Shield } from 'lucide-react'
import { authApi, membersApi } from '@/services/api'
import type { MemberResponse } from '@/types/api'
import { useApp } from '@/context/AppContext'

export default function LoginPage() {
  const { login, currentMember, showToast } = useApp()
  const navigate = useNavigate()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [selectedName, setSelectedName] = useState('')
  const [pin, setPin] = useState('')
  const [loading, setLoading] = useState(false)
  const [membersLoading, setMembersLoading] = useState(true)

  // 已登录则跳首页
  useEffect(() => {
    if (currentMember) navigate('/', { replace: true })
  }, [currentMember, navigate])

  useEffect(() => {
    membersApi.list()
      .then((rows) => {
        setMembers(rows)
        if (rows.length > 0) setSelectedName(rows[0].name)
      })
      .catch(() => showToast('无法加载成员列表', 'error'))
      .finally(() => setMembersLoading(false))
  }, [showToast])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedName || !pin) return
    setLoading(true)
    try {
      const { access_token, member } = await authApi.login({ member_name: selectedName, pin })
      login(member, access_token)
      showToast(`欢迎回来，${member.name}！`, 'success')
      navigate('/', { replace: true })
    } catch (err: any) {
      showToast(err.message ?? '登录失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)',
      padding: '24px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
      }}>
        {/* Logo 区 */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 64,
            height: 64,
            borderRadius: 18,
            background: 'linear-gradient(135deg, var(--color-accent), var(--color-income))',
            marginBottom: 16,
            boxShadow: '0 8px 24px rgba(99,102,241,0.35)',
          }}>
            <Shield size={32} color="white" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
            TeamLedgerBot
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>请选择成员并输入 PIN 登录</p>
        </div>

        {/* 登录卡片 */}
        <div className="glass-card" style={{ padding: 32 }}>
          <form onSubmit={submit}>
            <div className="form-group" style={{ marginBottom: 20 }}>
              <label className="form-label">选择成员</label>
              {membersLoading ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 14, padding: '10px 0' }}>正在加载成员列表...</div>
              ) : (
                <select
                  id="login-member-select"
                  className="form-input"
                  value={selectedName}
                  onChange={(e) => setSelectedName(e.target.value)}
                  required
                >
                  {members.map((m) => (
                    <option key={m.id} value={m.name}>
                      {m.name}{m.is_admin ? ' （管理员）' : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="form-group" style={{ marginBottom: 28 }}>
              <label className="form-label">PIN 码</label>
              <input
                id="login-pin-input"
                className="form-input"
                type="password"
                inputMode="numeric"
                pattern="[0-9]{4,8}"
                minLength={4}
                maxLength={8}
                placeholder="输入 4~8 位 PIN"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              id="login-submit-btn"
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px', fontSize: 15, gap: 8, justifyContent: 'center' }}
              disabled={loading || membersLoading}
            >
              <LogIn size={18} />
              {loading ? '验证中...' : '登录'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, color: 'var(--text-muted)', fontSize: 12 }}>
          首次使用请联系管理员设置 PIN
        </p>
      </div>
    </div>
  )
}
