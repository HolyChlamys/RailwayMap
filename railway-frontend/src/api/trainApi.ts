import apiClient from './client'
import type { Train } from '../types/train'
import { mapToTrain, mapToTrainDetail } from '../types/train'

export const trainApi = {
  async getByNo(no: string): Promise<Train> {
    const data: any = await apiClient.get(`/trains/${encodeURIComponent(no)}/route`)
    return mapToTrainDetail(data)
  },

  async search(query: string, limit = 8): Promise<Train[]> {
    const data: any[] = await apiClient.get('/trains/search', { params: { q: query, limit } })
    return data.map(mapToTrain)
  },
}
