import axios from 'axios'

const baseURL = (import.meta.env.VITE_API_BASE_URL ?? '').trim()

const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — 自动附加 Bearer Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — 全局错误标准化，401 自动跳转登录
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除本地认证状态，跳转登录页
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_member')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    const message =
      error.response?.data?.detail ??
      error.message ??
      '请求失败，请稍后重试'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
