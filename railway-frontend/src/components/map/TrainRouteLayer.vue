<script setup lang="ts">
import { watch } from 'vue'
import { useMapStore } from '../../stores/mapStore'
import type maplibregl from 'maplibre-gl'

const props = defineProps<{ map: maplibregl.Map | null; geoJsonData: object | null }>()
const mapStore = useMapStore()

watch(() => props.geoJsonData, (data) => {
  if (!props.map || !data) return

  const map = props.map
  const sourceId = 'highlighted-route'

  // 移除旧图层
  if (map.getLayer('highlighted-route-line')) {
    map.removeLayer('highlighted-route-line')
  }
  if (map.getLayer('highlighted-route-glow')) {
    map.removeLayer('highlighted-route-glow')
  }
  if (map.getSource(sourceId)) {
    map.removeSource(sourceId)
  }

  // 添加新的 GeoJSON 源
  map.addSource(sourceId, {
    type: 'geojson',
    data: data as any
  })

  // 发光效果
  map.addLayer({
    id: 'highlighted-route-glow',
    type: 'line',
    source: sourceId,
    paint: {
      'line-color': '#ff481a',
      'line-width': ['interpolate', ['linear'], ['zoom'], 6, 4, 14, 8],
      'line-opacity': 0.3,
      'line-blur': 3
    }
  })

  // 主路线
  map.addLayer({
    id: 'highlighted-route-line',
    type: 'line',
    source: sourceId,
    layout: {
      'line-join': 'round',
      'line-cap': 'round'
    },
    paint: {
      'line-color': [
        'match', ['get', 'confidence'],
        0.5, '#f39c12',
        1.0, '#ff481a',
        '#ff481a'
      ],
      'line-width': ['interpolate', ['linear'], ['zoom'], 6, 2.5, 14, 5],
      'line-opacity': 0.9,
      'line-dasharray': [
        'match', ['get', 'match_method'],
        'distance', ['literal', [3, 2]],
        ['literal', [1]]
      ]
    }
  })
})
</script>

<template>
  <div />
</template>
