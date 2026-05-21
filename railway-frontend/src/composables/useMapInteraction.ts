import { onMounted, onUnmounted } from 'vue'
import type { Map, MapMouseEvent } from 'maplibre-gl'

interface InteractionOptions {
  /** Callback when user clicks a station symbol on the map */
  onStationClick?: (stationId: string, e: MapMouseEvent) => void
  /** Callback when user clicks on empty map area */
  onMapBackgroundClick?: (e: MapMouseEvent) => void
  /** Callback when user hovers over a station */
  onStationHover?: (stationId: string | null) => void
}

/**
 * Composable for map interaction events.
 * Connects MapLibre layer events (click/hover on symbol layers)
 * to higher-level Vue logic (open panels, show tooltips).
 */
export function useMapInteraction(mapRef: () => Map | null, opts: InteractionOptions = {}) {
  const layerId = 'station-circles'

  function handleClick(e: MapMouseEvent) {
    const map = mapRef()
    if (!map) return

    const features = map.queryRenderedFeatures(e.point, { layers: [layerId] })
    if (features.length > 0) {
      const rawId = features[0].properties?.id
      const stationId = rawId != null ? String(rawId) : null
      if (stationId && opts.onStationClick) {
        opts.onStationClick(stationId, e)
      }
    } else {
      opts.onMapBackgroundClick?.(e)
    }
  }

  function handleMouseMove(e: MapMouseEvent) {
    const map = mapRef()
    if (!map) return

    const features = map.queryRenderedFeatures(e.point, { layers: [layerId] })
    if (features.length > 0) {
      map.getCanvas().style.cursor = 'pointer'
      const rawId = features[0].properties?.id
      const stationId = rawId != null ? String(rawId) : null
      opts.onStationHover?.(stationId)
    } else {
      map.getCanvas().style.cursor = ''
      opts.onStationHover?.(null)
    }
  }

  onMounted(() => {
    const map = mapRef()
    if (!map) return

    map.on('click', handleClick)
    map.on('mousemove', handleMouseMove)
  })

  onUnmounted(() => {
    const map = mapRef()
    if (!map) return

    map.off('click', handleClick)
    map.off('mousemove', handleMouseMove)
  })
}
