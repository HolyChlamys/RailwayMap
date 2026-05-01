<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useMapStore } from '../../stores/mapStore'

const mapStore = useMapStore()
const container = ref<HTMLDivElement>()
let map: maplibregl.Map | null = null

onMounted(() => {
  if (!container.value) return

  map = new maplibregl.Map({
    container: container.value,
    style: 'https://api.maptiler.com/maps/streets-v2/style.json?key=4WTGrPaI9R4eeeH5Oqhd',
    center: mapStore.center,
    zoom: mapStore.zoom,
    minZoom: 4,
    maxZoom: 18
  })

  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  map.on('load', () => {
    // 铁路线矢量瓦片源
    map!.addSource('railways', {
      type: 'vector',
      tiles: ['/api/tiles/railways/{z}/{x}/{y}.pbf'],
      minzoom: 6,
      maxzoom: 18
    })

    map!.addLayer({
      id: 'railways-layer',
      type: 'line',
      source: 'railways',
      'source-layer': 'railways',
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': [
          'match', ['get', 'category'],
          'high_speed',      '#ff481a',
          'rapid_transit',   '#ffa31a',
          'passenger_rail',  '#6ed568',
          'freight_rail',    '#d3ff4f',
          'other_rail',      '#708bbb',
          'subway',          '#85C1E9',
          '#e74c3c'
        ],
        'line-width': [
          'interpolate', ['linear'], ['zoom'],
          6, ['match', ['get', 'category'],
            'high_speed', 1.5, 'rapid_transit', 1.2, 'conventional', 1.0, 0.8],
          10, ['match', ['get', 'category'],
            'high_speed', 3.0, 'rapid_transit', 2.5, 'conventional', 2.0, 1.5],
          14, ['match', ['get', 'category'],
            'high_speed', 4.5, 'rapid_transit', 3.5, 'conventional', 3.0, 2.5]
        ],
        'line-opacity': 0.85,
        'line-dasharray': [
          'match', ['get', 'category'],
          'other_rail', ['literal', [3, 2]],
          ['literal', [1]]
        ]
      }
    })

    // 车站矢量瓦片源
    map!.addSource('stations', {
      type: 'vector',
      tiles: ['/api/tiles/stations/{z}/{x}/{y}.pbf'],
      minzoom: 8,
      maxzoom: 18
    })

    map!.addLayer({
      id: 'stations-layer',
      type: 'circle',
      source: 'stations',
      'source-layer': 'stations',
      paint: {
        'circle-color': [
          'match', ['get', 'category'],
          'major_hub',        '#e74c3c',
          'major_passenger',  '#e74c3c',
          'medium_passenger', '#f39c12',
          'small_passenger',  '#f39c12',
          'small_non_passenger', '#95a5a6',
          'large_yard',       '#3498db',
          'medium_yard',      '#3498db',
          'major_freight',    '#8B4513',
          'freight_yard',     '#8B4513',
          'signal_station',   '#27ae60',
          'emu_depot',        '#9b59b6',
          '#95a5a6'
        ],
        'circle-radius': [
          'interpolate', ['linear'], ['zoom'],
          8, ['match', ['get', 'category'],
            'major_hub', 4, 'major_passenger', 3, 'medium_passenger', 2, 'large_yard', 2, 1.5],
          12, ['match', ['get', 'category'],
            'major_hub', 8, 'major_passenger', 7, 'medium_passenger', 5, 'large_yard', 5, 3],
          16, ['match', ['get', 'category'],
            'major_hub', 14, 'major_passenger', 12, 'medium_passenger', 9, 'large_yard', 9, 6]
        ],
        'circle-opacity': 0.9,
        'circle-stroke-width': 1,
        'circle-stroke-color': '#ffffff'
      }
    })

    // 车站标签
    map!.addLayer({
      id: 'station-labels',
      type: 'symbol',
      source: 'stations',
      'source-layer': 'stations',
      minzoom: 10,
      layout: {
        'text-field': ['get', 'name'],
        'text-font': ['Noto Sans CJK SC Regular', 'Arial Unicode MS Regular'],
        'text-size': 11,
        'text-offset': [0, 1.5],
        'text-anchor': 'top',
        'text-allow-overlap': false
      },
      paint: {
        'text-color': '#333333',
        'text-halo-color': '#ffffff',
        'text-halo-width': 2
      }
    })

    map!.addLayer({
      id: 'station-labels-en',
      type: 'symbol',
      source: 'stations',
      'source-layer': 'stations',
      minzoom: 12,
      layout: {
        'text-field': ['get', 'city'],
        'text-font': ['Noto Sans CJK SC Regular', 'Arial Unicode MS Regular'],
        'text-size': 9,
        'text-offset': [0, 2.8],
        'text-anchor': 'top',
        'text-allow-overlap': false
      },
      paint: {
        'text-color': '#888888',
        'text-halo-color': '#ffffff',
        'text-halo-width': 1.5
      }
    })
  })

  map.on('moveend', () => {
    if (map) {
      mapStore.setCenter(map.getCenter().lng, map.getCenter().lat)
      mapStore.setZoom(Math.round(map.getZoom()))
    }
  })
})

onUnmounted(() => {
  map?.remove()
})

function flyTo(lon: number, lat: number, zoom: number) {
  map?.flyTo({ center: [lon, lat], zoom, duration: 1200 })
}

defineExpose({ flyTo })
</script>

<template>
  <div ref="container" class="w-full h-full" />
</template>
