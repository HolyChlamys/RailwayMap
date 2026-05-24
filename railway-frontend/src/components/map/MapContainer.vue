<script setup lang="ts">
import { watch, onUnmounted, ref, computed, shallowRef } from 'vue'
import { useMap } from '../../composables/useMap'
import { useMapInteraction } from '../../composables/useMapInteraction'
import { useMapDynamicResponse } from '../../composables/useMapDynamicResponse'
import { useMapStore } from '../../stores/mapStore'
import { useStationStore } from '../../stores/stationStore'
import { useRoutePlanStore } from '../../stores/routePlanStore'
import MapLoadingOverlay from './MapLoadingOverlay.vue'
import TrainRouteLayer from './TrainRouteLayer.vue'

const mapStore = useMapStore()
const stationStore = useStationStore()
const routePlanStore = useRoutePlanStore()

const mapRef = shallowRef<any>(null)
// Plain object with getter: prevents Vue template auto-unwrapping (keeps { value: Map | null } shape)
// while staying in sync with the underlying shallowRef. Required by TrainRouteLayer and useMapDynamicResponse.
const mapHolder = { get value() { return mapRef.value } }

const emit = defineEmits<{
  (e: 'station-click', id: number): void
  (e: 'map-background-click'): void
}>()
const hoveredFeatureKey = ref<string | null>(null)
const tooltip = ref<{ x: number; y: number; name: string; category: string } | null>(null)

// ---- Railway layer definitions (trunk/branch/spur tiers) ----
interface RailwayLayer {
  id: string
  displayGroup: 'trunk' | 'branch' | 'spur'
  categories?: string[]
  color: string
  baseWidth: number
  dashed: boolean
  minzoom: number
}

const RAILWAY_LAYERS: RailwayLayer[] = [
  { id: 'railway-trunk-hs', displayGroup: 'trunk', categories: ['high_speed'],                  color: '#ff3300', baseWidth: 3.0, dashed: false, minzoom: 2 },
  { id: 'railway-trunk-cv', displayGroup: 'trunk', categories: ['conventional', 'passenger_rail'], color: '#33a02c', baseWidth: 2.2, dashed: false, minzoom: 2 },
  { id: 'railway-branch',   displayGroup: 'branch',                                             color: '#6464b5', baseWidth: 1.5, dashed: true,  minzoom: 2 },
  { id: 'railway-spur',     displayGroup: 'spur',                                               color: '#6464b5', baseWidth: 0.8, dashed: true,  minzoom: 2 },
]

const RAILWAY_TILE_SOURCE = 'railway-tiles'
const STATION_TILE_SOURCE = 'station-tiles'

// ---- Map setup ----
const {
  map, isLoaded, loadProgress,
  flyTo, fitBounds, easeTo,
  addSource, removeSource, addLayer, removeLayer,
  setLayerVisibility, setLayerPaint,
  onClick, onMouseEnter, onMouseLeave,
  getMap,
} = useMap({
  containerId: 'map-canvas',
  onLoad: (m) => {
    addCustomLayers(m)

    // Entry animation sequence
    mapStore.setEntryPhase('background')
    setTimeout(() => mapStore.setEntryPhase('lines'), 400)
    setTimeout(() => mapStore.setEntryPhase('stations'), 900)
    setTimeout(() => mapStore.setEntryPhase('ui'), 1400)
    setTimeout(() => mapStore.setEntryPhase('complete'), 1800)

    // Re-add custom layers after style changes (e.g. dark/light toggle)
    m.on('styledata', () => {
      if (m.isStyleLoaded()) {
        addCustomLayers(m)
      }
    })

    // Hover highlight + tooltip on station circles
    m.on('mouseenter', 'station-circles', (e: any) => {
      m.getCanvas().style.cursor = 'pointer'
      if (e.features && e.features.length > 0) {
        setHover(m, e.features[0], e)
      }
    })
    m.on('mouseleave', 'station-circles', () => {
      m.getCanvas().style.cursor = ''
      clearHover(m)
    })

    mapRef.value = m
  },
})

// ---- Map interaction (click → StationPanel) ----
useMapInteraction(
  () => getMap(),
  {
    onStationClick: (stationId: string) => {
      emit('station-click', Number(stationId))
    },
    onMapBackgroundClick: () => {
      emit('map-background-click')
    },
  },
)

// ---- Hover highlight + tooltip helpers ----
function clearHover(m: any) {
  if (hoveredFeatureKey.value) {
    m.removeFeatureState({ source: STATION_TILE_SOURCE, sourceLayer: 'stations', id: hoveredFeatureKey.value })
    hoveredFeatureKey.value = null
  }
  tooltip.value = null
}

function setHover(m: any, feature: any, e: any) {
  const fid = feature.id
  if (fid == null) return
  if (hoveredFeatureKey.value === String(fid)) return
  clearHover(m)
  m.setFeatureState({ source: STATION_TILE_SOURCE, sourceLayer: 'stations', id: fid }, { hover: true })
  hoveredFeatureKey.value = String(fid)
  tooltip.value = {
    x: e.point.x,
    y: e.point.y,
    name: feature.properties?.name || '',
    category: feature.properties?.category || '',
  }
}

// ---- Add custom layers to the map ----
function makeFilter(rl: RailwayLayer): any[] {
  // Trunk layers: filter by display_group + category
  if (rl.categories && rl.categories.length > 0) {
    return [
      'all',
      ['==', 'display_group', rl.displayGroup],
      // Filter 'in' uses variadic args: ["in", key, v0, v1, ...]
      ['in', 'category', ...rl.categories],
    ]
  }
  // Branch / spur layers: filter by display_group only
  return ['==', 'display_group', rl.displayGroup]
}

function addCustomLayers(m: any) {
  if (m.getSource(RAILWAY_TILE_SOURCE)) return

  const isDark = (m.getStyle()?.name ?? '').includes('Dark')
  const tileBase = window.location.origin

  // 1. Railway vector tile source
  m.addSource(RAILWAY_TILE_SOURCE, {
    type: 'vector',
    tiles: [`${tileBase}/api/tiles/railways/{z}/{x}/{y}.pbf?v=3`],
    scheme: 'xyz',
    tileSize: 512,
    minzoom: 2,
    maxzoom: 16,
  })

  // Add one line layer per railway tier
  const lineBase = { type: 'line', source: RAILWAY_TILE_SOURCE, 'source-layer': 'railways' }
  RAILWAY_LAYERS.forEach((rl) => {
    m.addLayer({
      ...lineBase,
      id: rl.id,
      minzoom: rl.minzoom,
      filter: makeFilter(rl),
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: {
        'line-color': rl.color,
        'line-width': ['interpolate', ['linear'], ['zoom'],
          2, rl.baseWidth * 0.3,
          5, rl.baseWidth * 0.6,
          8, rl.baseWidth * 1.0,
          12, rl.baseWidth * 1.5,
          16, rl.baseWidth * 2.0],
        'line-opacity': ['interpolate', ['linear'], ['zoom'],
          rl.minzoom, 0,
          rl.minzoom + 0.5, 0.9],
        ...(rl.dashed ? { 'line-dasharray': [6, 4] } : {}),
      },
    })
  })

  // 2. Station vector tile source
  m.addSource(STATION_TILE_SOURCE, {
    type: 'vector',
    tiles: [`${tileBase}/api/tiles/stations/{z}/{x}/{y}.pbf?v=3`],
    scheme: 'xyz',
    tileSize: 512,
    minzoom: 4,
    maxzoom: 16,
    promoteId: 'id',
  })

  m.addLayer({
    id: 'station-circles',
    type: 'circle',
    source: STATION_TILE_SOURCE,
    'source-layer': 'stations',
    minzoom: 4,
    paint: {
      'circle-radius': ['case',
        ['boolean', ['feature-state', 'hover'], false],
        ['match', ['get', 'category'],
          'major_hub', 10, 'major_passenger', 8,
          'medium_passenger', 7, 'small_passenger', 6, 5],
        ['match', ['get', 'category'],
          'major_hub', 6, 'major_passenger', 5,
          'medium_passenger', 4, 'small_passenger', 3, 2.5],
      ],
      'circle-color': ['match', ['get', 'category'],
        'major_hub', '#d63031',
        'major_passenger', '#0066ff',
        'medium_passenger', '#0066ff',
        'small_passenger', '#3388ff',
        '#0066ff'],
      'circle-stroke-width': ['case',
        ['boolean', ['feature-state', 'hover'], false], 3, 1.5,
      ],
      'circle-stroke-color': ['case',
        ['boolean', ['feature-state', 'hover'], false], '#ffd700', '#fff',
      ],
      'circle-opacity': ['interpolate', ['linear'], ['zoom'],
        5, 0.5,
        7, 0.9],
    },
  })

  m.addLayer({
    id: 'station-labels',
    type: 'symbol',
    source: STATION_TILE_SOURCE,
    'source-layer': 'stations',
    minzoom: 7,
    layout: {
      'text-field': ['get', 'name'],
      'text-font': ['Noto Sans SC Regular', 'PingFang SC Regular'],
      'text-size': 11,
      'text-offset': [0, 1.6],
      'text-anchor': 'top',
    },
    paint: {
      'text-color': isDark ? '#d0ccc6' : '#2d2a26',
      'text-halo-color': isDark ? 'rgba(26,26,30,0.7)' : 'rgba(255,255,255,0.85)',
      'text-halo-width': 2.5,
    },
  })

  applyLayerVisibility(m)
}

// ---- Sync layer visibility from store to MapLibre ----
const VIS_KEY_TO_LAYER: Record<string, string> = {
  trunk_hs: 'railway-trunk-hs',
  trunk_cv: 'railway-trunk-cv',
  branch: 'railway-branch',
  spur: 'railway-spur',
}

function applyLayerVisibility(m: any) {
  const vis = mapStore.layerVisibility.lines
  for (const [key, layerId] of Object.entries(VIS_KEY_TO_LAYER)) {
    if (m.getLayer(layerId)) {
      m.setLayoutProperty(layerId, 'visibility', vis[key] ? 'visible' : 'none')
    }
  }
}

watch(
  () => mapStore.layerVisibility.lines,
  () => {
    const m = getMap()
    if (!m || !isLoaded.value) return
    applyLayerVisibility(m)
  },
  { deep: true },
)

// ---- City focus watcher ----
watch(
  () => mapStore.focusCity,
  (city) => {
    const m = getMap()
    if (!m || !isLoaded.value) return

    if (!city) {
      // Reset — show all stations normally, with hover feature-state support
      m.setPaintProperty('station-circles', 'circle-opacity', ['interpolate', ['linear'], ['zoom'], 5, 0.5, 7, 0.9])
      m.setPaintProperty('station-circles', 'circle-color', ['match', ['get', 'category'],
        'major_hub', '#d63031',
        'major_passenger', '#0066ff',
        'medium_passenger', '#0066ff',
        'small_passenger', '#3388ff',
        '#0066ff'])
      m.setPaintProperty('station-circles', 'circle-radius', ['case',
        ['boolean', ['feature-state', 'hover'], false],
        ['match', ['get', 'category'],
          'major_hub', 10, 'major_passenger', 8,
          'medium_passenger', 7, 'small_passenger', 6, 5],
        ['match', ['get', 'category'],
          'major_hub', 6, 'major_passenger', 5,
          'medium_passenger', 4, 'small_passenger', 3, 2.5],
      ])
      m.setPaintProperty('station-circles', 'circle-stroke-width', ['case',
        ['boolean', ['feature-state', 'hover'], false], 3, 1.5,
      ])
      m.setPaintProperty('station-circles', 'circle-stroke-color', ['case',
        ['boolean', ['feature-state', 'hover'], false], '#ffd700', '#fff',
      ])
      m.setPaintProperty('station-labels', 'text-opacity', 1)
      return
    }

    // Normalize city name (strip 市/省 suffix)
    const cityClean = city.replace('市', '').replace('省', '')

    // Find visible stations in this city to compute bounds
    const features = m.queryRenderedFeatures({ layers: ['station-circles'] })
    const cityFeatures = features.filter((f: any) => {
      const c = f.properties?.city || ''
      return c === city || c === cityClean
    })

    if (cityFeatures.length > 0) {
      let minLng = 180, maxLng = -180, minLat = 90, maxLat = -90
      cityFeatures.forEach((f: any) => {
        const [lng, lat] = f.geometry.coordinates
        minLng = Math.min(minLng, lng); maxLng = Math.max(maxLng, lng)
        minLat = Math.min(minLat, lat); maxLat = Math.max(maxLat, lat)
      })
      m.fitBounds(
        [[minLng, minLat], [maxLng, maxLat]] as any,
        { padding: 120, duration: 1000 },
      )
    }

    // Highlight matched stations, dim others
    const cityMatch = ['any', ['==', ['get', 'city'], city], ['==', ['get', 'city'], cityClean]]

    m.setPaintProperty('station-circles', 'circle-opacity', [
      'case', cityMatch, 0.95, 0.15,
    ])
    m.setPaintProperty('station-circles', 'circle-color', [
      'case', cityMatch, '#0984e3', '#95a5a6',
    ])
    m.setPaintProperty('station-circles', 'circle-radius', ['case',
      ['boolean', ['feature-state', 'hover'], false],
      ['case', cityMatch, 12, 6],
      ['case', cityMatch, 8, 2.5],
    ])
    m.setPaintProperty('station-circles', 'circle-stroke-width', ['case',
      ['boolean', ['feature-state', 'hover'], false], 3, 1.5,
    ])
    m.setPaintProperty('station-circles', 'circle-stroke-color', ['case',
      ['boolean', ['feature-state', 'hover'], false], '#ffd700', '#fff',
    ])
    m.setPaintProperty('station-labels', 'text-opacity', [
      'case', cityMatch, 1, 0,
    ])
  },
)

// ---- Active Routes for TrainRouteLayer ----
const activeRoutes = computed(() => {
  const indices = routePlanStore.activePlanIndices
  return indices.map(i => routePlanStore.plans[i]).filter(Boolean)
})

// ---- Map Dynamic Response System (Focus Watchers) ----
useMapDynamicResponse(mapHolder)

// ---- Sync viewport changes back to store ----
watch(isLoaded, (loaded) => {
  if (!loaded) return
  const m = getMap()
  if (!m) return

  m.on('moveend', () => {
    const c = m.getCenter()
    mapStore.setViewport({
      center: [c.lng, c.lat],
      zoom: m.getZoom(),
      bearing: m.getBearing(),
      pitch: m.getPitch(),
    })
  })
})

onUnmounted(() => {
  mapStore.setEntryPhase('idle')
})

defineExpose({
  flyTo, fitBounds, easeTo,
  addSource, removeSource, addLayer, removeLayer,
  setLayerVisibility, setLayerPaint,
  onClick, onMouseEnter, onMouseLeave,
  getMap,
})
</script>

<template>
  <div class="map-container">
    <div id="map-canvas" class="map-canvas" />
    <MapLoadingOverlay />

    <!-- Station hover tooltip -->
    <div
      v-if="tooltip"
      class="station-tooltip"
      :style="{ left: tooltip.x + 16 + 'px', top: tooltip.y - 40 + 'px' }"
    >
      <span class="tooltip-name">{{ tooltip.name }}</span>
      <span class="tooltip-cat">{{ tooltip.category }}</span>
    </div>

    <!-- Zoom level indicator -->
    <div class="zoom-indicator">z{{ mapStore.viewport.zoom.toFixed(1) }}</div>

    <!-- Train Route Animations -->
    <TrainRouteLayer :mapRef="mapHolder" :routes="activeRoutes" />
  </div>
</template>

<style scoped>
.map-container { position: absolute; inset: 0; }
.map-canvas { width: 100%; height: 100%; }
:deep(.maplibregl-ctrl-attrib) {
  position: absolute;
  bottom: var(--space-2);
  left: var(--space-2);
  font-size: 10px;
  opacity: 0.6;
}

.station-tooltip {
  position: absolute;
  z-index: 200;
  pointer-events: none;
  background: var(--glass-bg, rgba(28, 28, 30, 0.92));
  backdrop-filter: blur(10px);
  color: #fff;
  padding: 4px 10px;
  border-radius: var(--radius-sm, 6px);
  font-size: 13px;
  line-height: 1.4;
  white-space: nowrap;
  box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.3));
  border: 1px solid rgba(255,255,255,0.12);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.tooltip-name {
  font-weight: 600;
  font-family: var(--font-sans, 'PingFang SC', sans-serif);
}

.tooltip-cat {
  font-size: 10px;
  opacity: 0.65;
  text-transform: capitalize;
}

.zoom-indicator {
  position: absolute;
  bottom: var(--space-3);
  right: var(--space-3);
  z-index: 100;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(28, 28, 30, 0.75);
  backdrop-filter: blur(6px);
  color: #fff;
  font-size: 11px;
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>