import apiClient from './client'
import type { Station, StationSearchResult } from '../types/station'
import { mapToStation, mapToSearchResult } from '../types/station'

export const stationApi = {
  async getById(id: number): Promise<Station> {
    const data: any = await apiClient.get(`/stations/${id}`)
    return mapToStation(data)
  },

  async search(query: string, limit = 8): Promise<StationSearchResult[]> {
    const data: any[] = await apiClient.get('/stations/search', { params: { q: query, limit } })
    return data.map(mapToSearchResult)
  },

  async getByCity(city: string): Promise<StationSearchResult[]> {
    const data: any[] = await apiClient.get(`/stations/city/${encodeURIComponent(city)}`)
    return data.map(mapToSearchResult)
  },
}
