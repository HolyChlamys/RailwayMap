import api from './api'
import type { TransferRequest, TransferResult } from '../types/transfer'

export function searchTransfer(request: TransferRequest) {
  return api.post<{
    results: TransferResult[]
    total_found: number
    search_time_ms: number
  }>('/transfer/search', request)
}
