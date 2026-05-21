import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MapViewport, MapEntryPhase, LayerVisibility } from '../types/map'

export const useMapStore = defineStore('map', () => {
  // ---- Viewport State ----
  const viewport = ref<MapViewport>({
    center: [108.0, 30.0],
    zoom: 4.2,
    bearing: 0,
    pitch: 0,
  })

  function setViewport(v: Partial<MapViewport>) {
    Object.assign(viewport.value, v)
  }

  // ---- Entry Animation ----
  const entryPhase = ref<MapEntryPhase>('idle')

  function setEntryPhase(phase: MapEntryPhase) {
    entryPhase.value = phase
  }

  const isEntryComplete = computed(() => entryPhase.value === 'complete')

  // ---- Layer Visibility ----
  const layerVisibility = ref<LayerVisibility>({
    stations: {
      major_hub: true,
      major_passenger: true,
      medium_passenger: true,
      small_passenger: true,
      large_yard: true,
      freight: false,
    },
    lines: {
      trunk_hs: true,
      trunk_cv: true,
      branch: true,
      spur: false,
    },
  })

  function toggleStationType(type: string) {
    layerVisibility.value.stations[type] = !layerVisibility.value.stations[type]
  }

  function toggleLineType(type: string) {
    layerVisibility.value.lines[type] = !layerVisibility.value.lines[type]
  }

  // ---- Current Focus ----
  const focusCity = ref<string | null>(null)
  const focusStationId = ref<string | null>(null)
  const focusTrainNo = ref<string | null>(null)

  function setFocusCity(city: string | null) { focusCity.value = city }
  function setFocusStation(id: string | null) { focusStationId.value = id }
  function setFocusTrain(no: string | null) { focusTrainNo.value = no }

  function clearAllFocus() {
    focusCity.value = null
    focusStationId.value = null
    focusTrainNo.value = null
  }

  return {
    viewport,
    setViewport,
    entryPhase,
    setEntryPhase,
    isEntryComplete,
    layerVisibility,
    toggleStationType,
    toggleLineType,
    focusCity,
    focusStationId,
    focusTrainNo,
    setFocusCity,
    setFocusStation,
    setFocusTrain,
    clearAllFocus,
  }
})
