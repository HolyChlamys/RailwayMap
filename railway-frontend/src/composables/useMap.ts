import { shallowRef, ref, onMounted, onUnmounted } from 'vue'
import { Map, type MapOptions, type MapMouseEvent, type GeoJSONSourceSpecification, type LayerSpecification, type LngLatBoundsLike } from 'maplibre-gl'

export interface UseMapOptions {
  /** CSS selector or element ID for the map container */
  containerId: string
  /** Override default map options */
  mapOptions?: Partial<MapOptions>
  /** Callback when map 'load' event fires */
  onLoad?: (map: Map) => void
}

export function useMap(options: UseMapOptions) {
  const { containerId, mapOptions = {}, onLoad } = options

  const map = shallowRef<Map | null>(null)
  const isLoaded = ref(false)
  const loadProgress = ref(0)

  // ---- Lifecycle ----
  onMounted(() => {
    const defaults: MapOptions = {
      container: containerId,
      style: '/map-style.json',
      center: [108.0, 30.0],
      zoom: 4.2,
      minZoom: 2.5,
      maxZoom: 18,
      maxBounds: [[72, 0], [136, 55]] as LngLatBoundsLike,
      attributionControl: false,
      ...mapOptions,
    }

    const instance = new Map(defaults)

    // Progress simulation for entry animation
    let progressTimer: ReturnType<typeof setInterval>
    progressTimer = setInterval(() => {
      if (loadProgress.value < 90) {
        loadProgress.value += Math.random() * 15 + 5
        if (loadProgress.value > 90) loadProgress.value = 90
      }
    }, 200)

    instance.on('load', () => {
      clearInterval(progressTimer)
      loadProgress.value = 100
      isLoaded.value = true
      onLoad?.(instance)
    })

    // Fallback: if map fails to load within 10s, show the app anyway
    setTimeout(() => {
      if (!isLoaded.value) {
        clearInterval(progressTimer)
        loadProgress.value = 100
        isLoaded.value = true
        console.warn('[useMap] Map load timed out — showing app with limited map functionality')
        onLoad?.(instance)
      }
    }, 10000)

    // Handle tile errors gracefully
    instance.on('error', (e) => {
      console.warn('[useMap] Map error:', e.error?.message ?? 'unknown')
    })

    map.value = instance
  })

  onUnmounted(() => {
    map.value?.remove()
    map.value = null
  })

  // ---- Map Navigation ----
  function flyTo(center: [number, number], zoom?: number, duration = 1200) {
    map.value?.flyTo({ center, zoom: zoom ?? map.value.getZoom(), duration })
  }

  function fitBounds(bounds: LngLatBoundsLike, padding = 80, duration = 1000) {
    map.value?.fitBounds(bounds, { padding, duration })
  }

  function easeTo(center: [number, number], zoom: number, duration = 600) {
    map.value?.easeTo({ center, zoom, duration })
  }

  // ---- Data Sources ----
  function addSource(id: string, source: GeoJSONSourceSpecification) {
    if (map.value?.getSource(id)) {
      const src = map.value.getSource(id) as any
      if (src && typeof src.setData === 'function') {
        src.setData(source.data)
      }
    } else {
      map.value?.addSource(id, source)
    }
  }

  function removeSource(id: string) {
    if (map.value?.getSource(id)) {
      map.value.removeSource(id)
    }
  }

  // ---- Layers ----
  function addLayer(layer: LayerSpecification, beforeId?: string) {
    if (map.value?.getLayer(layer.id)) {
      map.value.removeLayer(layer.id)
    }
    map.value?.addLayer(layer, beforeId)
  }

  function removeLayer(id: string) {
    if (map.value?.getLayer(id)) {
      map.value.removeLayer(id)
    }
  }

  function setLayerVisibility(id: string, visible: boolean) {
    if (!map.value?.getLayer(id)) return
    map.value.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none')
  }

  function setLayerPaint(id: string, property: string, value: any) {
    if (!map.value?.getLayer(id)) return
    map.value.setPaintProperty(id, property, value)
  }

  // ---- Events ----
  function onClick(handler: (e: MapMouseEvent) => void) {
    map.value?.on('click', handler)
  }

  function onMouseEnter(layerId: string, handler: (e: MapMouseEvent) => void) {
    map.value?.on('mouseenter', layerId, handler)
  }

  function onMouseLeave(layerId: string, handler: (e: MapMouseEvent) => void) {
    map.value?.on('mouseleave', layerId, handler)
  }

  function once(event: string, handler: Function) {
    map.value?.once(event, handler as any)
  }

  // ---- Utilities ----
  function getMap(): Map | null {
    return map.value
  }

  function project(lngLat: [number, number]) {
    return map.value?.project(lngLat as any) ?? { x: 0, y: 0 }
  }

  function unproject(point: { x: number; y: number }) {
    return map.value?.unproject(point as any) ?? { lng: 0, lat: 0 }
  }

  function getZoom(): number {
    return map.value?.getZoom() ?? 5
  }

  function getCenter(): [number, number] {
    const c = map.value?.getCenter()
    return [c?.lng ?? 104, c?.lat ?? 36.5]
  }

  return {
    // State
    map,
    isLoaded,
    loadProgress,

    // Navigation
    flyTo,
    fitBounds,
    easeTo,

    // Data
    addSource,
    removeSource,
    addLayer,
    removeLayer,
    setLayerVisibility,
    setLayerPaint,

    // Events
    onClick,
    onMouseEnter,
    onMouseLeave,
    once,

    // Utilities
    getMap,
    project,
    unproject,
    getZoom,
    getCenter,
  }
}
