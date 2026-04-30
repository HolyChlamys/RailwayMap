import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StationSearchResult } from '../types/station'
import type { TrainSearchResult } from '../types/train'

export const useSearchStore = defineStore('search', () => {
  const activeTab = ref<'station' | 'train' | 'transfer'>('station')
  const stationResults = ref<StationSearchResult[]>([])
  const trainResults = ref<TrainSearchResult[]>([])
  const searchQuery = ref('')
  const isSearching = ref(false)

  function setTab(tab: 'station' | 'train' | 'transfer') {
    activeTab.value = tab
  }

  function setQuery(q: string) {
    searchQuery.value = q
  }

  return { activeTab, stationResults, trainResults, searchQuery, isSearching, setTab, setQuery }
})
