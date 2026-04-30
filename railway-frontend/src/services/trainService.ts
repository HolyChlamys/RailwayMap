import api from './api'
import type { TrainSearchResult, TrainRouteDetail } from '../types/train'

export function searchTrains(q: string, type?: string, limit = 20) {
  return api.get<TrainSearchResult[]>('/trains/search', {
    params: { q, type, limit }
  })
}

export function getTrainRoute(no: string) {
  return api.get<TrainRouteDetail>(`/trains/${no}/route`)
}
