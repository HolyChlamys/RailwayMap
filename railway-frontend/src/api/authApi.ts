import apiClient from './client'

export interface AuthResponse {
  success: boolean
  token?: string
  message?: string
}

export const authApi = {
  login(username: string, password: string): Promise<AuthResponse> {
    return apiClient.post('/auth/login', { username, password }) as any
  },

  register(username: string, password: string): Promise<AuthResponse> {
    return apiClient.post('/auth/register', { username, password }) as any
  },
}
