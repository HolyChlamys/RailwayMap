import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { StationSearchResult, CityResult } from '../types/station'
import type { Train } from '../types/train'

export type SearchTab = 'station' | 'train' | 'city'

export interface SearchResultItem {
  type: 'station' | 'train' | 'city'
  /** Station search result */
  station?: StationSearchResult
  /** Train search result */
  train?: Train
  /** City search result */
  city?: CityResult
  /** Display label */
  label: string
  /** Subtitle (type/city info) */
  sub: string
  /** Action payload: station ID, train number, or city name */
  action: string
}

export const useSearchStore = defineStore('search', () => {
  // ---- State ----
  const activeTab = ref<SearchTab>('station')
  const query = ref('')
  const results = ref<SearchResultItem[]>([])
  const isDropdownOpen = ref(false)
  const loading = ref(false)

  // ---- Computed ----
  const placeholder = computed(() => {
    const map: Record<SearchTab, string> = {
      station: '搜索车站…',
      train: '搜索车次（如 G1、D301）…',
      city: '搜索城市（如 北京、上海）…',
    }
    return map[activeTab.value]
  })

  const hasResults = computed(() => results.value.length > 0)

  // ---- Actions ----
  function setTab(tab: SearchTab) {
    activeTab.value = tab
    query.value = ''
    results.value = []
  }

  function setQuery(q: string) {
    query.value = q
  }

  function setResults(r: SearchResultItem[]) {
    results.value = r
  }

  function openDropdown() {
    isDropdownOpen.value = true
  }

  function closeDropdown() {
    isDropdownOpen.value = false
  }

  function clear() {
    query.value = ''
    results.value = []
    isDropdownOpen.value = false
    loading.value = false
  }

  function setLoading(l: boolean) {
    loading.value = l
  }

  return {
    activeTab,
    query,
    results,
    isDropdownOpen,
    loading,
    placeholder,
    hasResults,
    setTab,
    setQuery,
    setResults,
    openDropdown,
    closeDropdown,
    clear,
    setLoading,
  }
})
