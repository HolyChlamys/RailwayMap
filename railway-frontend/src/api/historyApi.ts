import apiClient from './client'

export interface HistoryItem {
  id: number
  search_type: string
  query_text: string
  created_at: string
}

export const historyApi = {
  getAll(): Promise<HistoryItem[]> {
    return apiClient.get('/history') as any
  },

  add(searchType: string, queryText: string): Promise<any> {
    return apiClient.post('/history', { search_type: searchType, query_text: queryText }) as any
  },
}
