import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Station, StationSearchResult } from '../types/station'
import type { Train } from '../types/train'

export const useStationStore = defineStore('station', () => {
  // ---- State ----
  const currentStationId = ref<number | null>(null)
  const stationCache = ref<Map<number, Station>>(new Map())
  const allTrainsAtStation = ref<Train[]>([])
  const loading = ref(false)

  // ---- Computed ----
  const currentStation = computed<Station | null>(() => {
    if (currentStationId.value === null) return null
    return stationCache.value.get(currentStationId.value) ?? null
  })

  const hasStation = computed(() => currentStation.value !== null)

  // ---- Actions ----
  function setCurrentStation(id: number | null) {
    currentStationId.value = id
  }

  function cacheStation(station: Station) {
    stationCache.value.set(station.id, station)
  }

  function cacheSearchResults(results: StationSearchResult[]) {
    results.forEach((r) => {
      if (!stationCache.value.has(r.id)) {
        stationCache.value.set(r.id, {
          id: r.id,
          name: r.name,
          city: r.city,
          province: r.province,
          category: r.category,
          lon: r.lon,
          lat: r.lat,
        })
      }
    })
  }

  function getStation(id: number): Station | undefined {
    return stationCache.value.get(id)
  }

  function setAllTrains(trains: Train[]) {
    allTrainsAtStation.value = trains
  }

  function setLoading(l: boolean) {
    loading.value = l
  }

  function clear() {
    currentStationId.value = null
    allTrainsAtStation.value = []
  }

  return {
    currentStationId,
    stationCache,
    allTrainsAtStation,
    loading,
    currentStation,
    hasStation,
    setCurrentStation,
    cacheStation,
    cacheSearchResults,
    getStation,
    setAllTrains,
    setLoading,
    clear,
  }
})
