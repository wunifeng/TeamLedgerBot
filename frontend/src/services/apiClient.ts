import axios from 'axios'

const baseURL = (import.meta.env.VITE_API_BASE_URL ?? '').trim()

const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — can add auth token here in the future
apiClient.interceptors.request.use((config) => {
  return config
})

// Response interceptor — global error normalisation
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ??
      error.message ??
      '请求失败，请稍后重试'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
