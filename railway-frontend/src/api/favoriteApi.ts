import apiClient from './client'

export interface FavoriteItem {
  id: number
  type: 'station' | 'train'
  target_id: string
  label: string
  data?: any
  created_at: string
}

export const favoriteApi = {
  getAll(): Promise<FavoriteItem[]> {
    return apiClient.get('/favorites') as any
  },

  add(type: string, targetId: string, label: string, data?: Record<string, any>): Promise<any> {
    return apiClient.post('/favorites', { type, target_id: targetId, label, data: data ?? {} }) as any
  },

  remove(id: number): Promise<any> {
    return apiClient.delete(`/favorites/${id}`) as any
  },
}
