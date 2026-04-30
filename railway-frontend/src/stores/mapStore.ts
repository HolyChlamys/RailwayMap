import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMapStore = defineStore('map', () => {
  const center = ref<[number, number]>([108.5, 35.5])
  const zoom = ref(5)
  const selectedStationId = ref<number | null>(null)
  const highlightedTrainNo = ref<string | null>(null)
  const routeGeoJson = ref<object | null>(null)
  const layerVisibility = ref({
    railways: true,
    stations: true
  })

  function setCenter(lon: number, lat: number) {
    center.value = [lon, lat]
  }

  function setZoom(z: number) {
    zoom.value = z
  }

  function selectStation(id: number | null) {
    selectedStationId.value = id
  }

  function highlightTrain(no: string | null) {
    highlightedTrainNo.value = no
  }

  return {
    center, zoom, selectedStationId, highlightedTrainNo, routeGeoJson, layerVisibility,
    setCenter, setZoom, selectStation, highlightTrain
  }
})
