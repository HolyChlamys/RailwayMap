import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('[API]', error.message)
    return Promise.reject(error)
  }
)

export default api
