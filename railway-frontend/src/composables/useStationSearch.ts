import { watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { useSearchStore, type SearchResultItem } from '../stores/searchStore'
import { useStationStore } from '../stores/stationStore'
import { useTrainStore } from '../stores/trainStore'
import { stationApi } from '../api/stationApi'
import { trainApi } from '../api/trainApi'
import { STATION_TYPE_LABELS } from '../types/station'

/**
 * Composable that wires up the search store with real backend API calls.
 * Watches searchStore.query and populates results on change.
 */
export function useStationSearch() {
  const searchStore = useSearchStore()
  const stationStore = useStationStore()
  const trainStore = useTrainStore()

  // ---- Hot suggestions (no query) ----
  // Pre-fetch hot stations once
  let hotStationsLoaded = false
  async function loadHotStations() {
    if (hotStationsLoaded) return
    try {
      const names = ['北京', '上海虹桥', '广州南', '成都东', '西安北', '武汉']
      for (const name of names) {
        if (stationStore.stationCache.size === 0 || ![...stationStore.stationCache.values()].some(s => s.name === name)) {
          const results = await stationApi.search(name, 1)
          if (results.length > 0) stationStore.cacheSearchResults(results)
        }
      }
      hotStationsLoaded = true
    } catch { /* ignore */ }
  }

  function getHotStations(): SearchResultItem[] {
    const hotNames = ['北京', '上海虹桥', '广州南', '成都东', '西安北', '武汉']
    const results: SearchResultItem[] = []
    for (const name of hotNames) {
      let found = false
      stationStore.stationCache.forEach((s) => {
        if (s.name === name && !found) {
          found = true
          results.push({
            type: 'station' as const,
            station: { id: s.id, name: s.name, city: s.city || '', category: s.category, lon: s.lon, lat: s.lat },
            label: s.name,
            sub: `${s.city || ''} · ${STATION_TYPE_LABELS[s.category]}`,
            action: String(s.id),
          })
        }
      })
      if (!found) {
        results.push({ type: 'station' as const, label: name, sub: '', action: name })
      }
    }
    if (results.some(r => !r.station)) loadHotStations()
    return results
  }

  function getHotTrains(): SearchResultItem[] {
    const hotNos = ['G1', 'G2', 'G3', 'D301', 'G89', 'Z55']
    return hotNos.map(no => {
      const train = trainStore.getTrain(no)
      return {
        type: 'train' as const,
        train: train || undefined,
        label: no,
        sub: train ? `${train.from} → ${train.to}` : '热门车次',
        action: no,
      }
    })
  }

  function getHotCities(): SearchResultItem[] {
    const cities = ['北京', '上海', '广州', '成都', '西安', '武汉']
    return cities.map(city => ({
      type: 'city' as const,
      label: city,
      sub: '',
      action: city,
    }))
  }

  // ---- Show hot suggestions on initial load / dropdown open ----
  function showHotForTab() {
    const tab = searchStore.activeTab
    if (tab === 'station') searchStore.setResults(getHotStations())
    else if (tab === 'train') searchStore.setResults(getHotTrains())
    else searchStore.setResults(getHotCities())
  }
  // Set initial hot suggestions
  showHotForTab()

  // Refresh hot suggestions when dropdown opens with empty query
  watch(() => searchStore.isDropdownOpen, (open) => {
    if (open && !searchStore.query.trim()) showHotForTab()
  })

  // ---- Debounced search driver ----
  const performSearch = useDebounceFn(async () => {
    const q = searchStore.query.trim()
    const tab = searchStore.activeTab

    if (!q) {
      if (tab === 'station') searchStore.setResults(getHotStations())
      else if (tab === 'train') searchStore.setResults(getHotTrains())
      else searchStore.setResults(getHotCities())
      return
    }

    searchStore.setLoading(true)

    try {
      if (tab === 'station') {
        const results = await stationApi.search(q, 8)
        stationStore.cacheSearchResults(results)
        searchStore.setResults(results.map(r => ({
          type: 'station' as const,
          station: { id: r.id, name: r.name, city: r.city || '', category: r.category, lon: r.lon, lat: r.lat },
          label: r.name,
          sub: `${r.city || ''} · ${STATION_TYPE_LABELS[r.category]}`,
          action: String(r.id),
        })))
      } else if (tab === 'train') {
        const results = await trainApi.search(q, 8)
        results.forEach(t => trainStore.cacheTrain(t))
        searchStore.setResults(results.map(t => ({
          type: 'train' as const,
          train: t,
          label: t.no,
          sub: `${t.from} → ${t.to}`,
          action: t.no,
        })))
      } else if (tab === 'city') {
        // Search stations by city keyword, then aggregate
        const results = await stationApi.search(q, 100)
        const cityMap = new Map<string, number>()
        results.forEach(r => {
          const c = r.city || r.province || ''
          if (c) cityMap.set(c, (cityMap.get(c) ?? 0) + 1)
        })
        const cityResults = Array.from(cityMap.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 8)
          .map(([city, count]) => ({
            type: 'city' as const,
            label: city,
            sub: `${count} 个车站`,
            action: city,
          }))
        if (cityResults.length === 0 && q.length > 0) {
          // Fallback: direct city name match
          cityResults.push({ type: 'city' as const, label: q, sub: '', action: q })
        }
        searchStore.setResults(cityResults)
      }
    } catch (e: any) {
      console.warn('[useStationSearch] API error:', e.message)
      searchStore.setResults([])
    } finally {
      searchStore.setLoading(false)
    }
  }, 200)

  // Watch query and tab changes
  watch(
    () => [searchStore.query, searchStore.activeTab] as const,
    () => { performSearch() },
  )

  return { performSearch, getHotStations, getHotTrains, getHotCities }
}
