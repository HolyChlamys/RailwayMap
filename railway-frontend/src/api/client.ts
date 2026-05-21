import axios from 'axios'

const TOKEN_KEY = 'railwaymap_token'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — inject JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor — unwrap data, handle 401
apiClient.interceptors.response.use(
  (response) => response.data as any,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stale token on auth failure
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('railwaymap_user')
    }
    const message = error.response?.data?.message || error.message || '请求失败'
    console.error(`[API Error] ${error.config?.url}:`, message)
    return Promise.reject(new Error(message))
  },
)

export default apiClient
