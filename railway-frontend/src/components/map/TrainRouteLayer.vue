<script setup lang="ts">
import { watch } from 'vue'
import type { Map, GeoJSONSource } from 'maplibre-gl'
import type { RoutePlan } from '../../types/route'
import { useTrainAnimation } from '../../composables/useTrainAnimation'

const props = defineProps<{
  mapRef: { value: Map | null }
  routes: RoutePlan[]
}>()

const { startAnimation, stopAnimation, getTrainColor } = useTrainAnimation(props.mapRef)

watch(
  () => props.routes,
  (routes) => {
    stopAnimation()
    if (routes.length > 0) {
      addRouteSources(routes)
      startAnimation(routes)
    }
  },
  { deep: true },
)

function addRouteSources(routes: RoutePlan[]) {
  const map = props.mapRef.value
  if (!map) return

  const displayRoutes = routes.length > 3 ? routes.slice(0, 3) : routes
  const simplified = routes.length > 3

  displayRoutes.forEach((route) => {
    const sourceId = `route-${route.id}`
    const color = route.color || getTrainColor(route.segments[0]?.trainNo ?? null)

    const coords: [number, number][] = []
    route.segments.forEach(seg => {
      if (seg.coordinates) coords.push(...seg.coordinates)
    })

    if (coords.length < 2) return

    const geojson: GeoJSON.Feature = {
      type: 'Feature',
      properties: {},
      geometry: { type: 'LineString', coordinates: coords },
    }

    if (map.getSource(sourceId)) {
      (map.getSource(sourceId) as GeoJSONSource).setData(geojson as any)
    } else {
      map.addSource(sourceId, { type: 'geojson', data: geojson as any })

      map.addLayer({
        id: `${sourceId}-line`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': color,
          'line-width': simplified ? 2 : 3,
          'line-dasharray': simplified ? [4, 2] : [8, 6],
          'line-opacity': 0.9,
        },
      })

      const stationFeatures: GeoJSON.Feature[] = []
      route.segments.forEach((seg, idx) => {
        if (seg.coordinates && seg.coordinates.length > 0) {
          stationFeatures.push({
            type: 'Feature',
            properties: { isTerminal: idx === 0 || idx === route.segments.length - 1 },
            geometry: { type: 'Point', coordinates: seg.coordinates[0] },
          })
        }
      })

      map.addSource(`${sourceId}-stops`, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: stationFeatures } as any,
      })

      map.addLayer({
        id: `${sourceId}-stops-layer`,
        type: 'circle',
        source: `${sourceId}-stops`,
        paint: {
          'circle-color': color,
          'circle-radius': ['case', ['get', 'isTerminal'], 8, 5],
          'circle-stroke-width': ['case', ['get', 'isTerminal'], 2, 0],
          'circle-stroke-color': '#fff',
          'circle-opacity': 0.9,
        },
      })
    }
  })
}
</script>

<template>
  <div />
</template>
