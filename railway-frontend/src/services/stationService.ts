import api from './api'
import type { StationSearchResult } from '../types/station'

export function searchStations(q: string, city?: string, limit = 20) {
  return api.get<StationSearchResult[]>('/stations/search', {
    params: { q, city, limit }
  })
}

export function getStation(id: number) {
  return api.get(`/stations/${id}`)
}
