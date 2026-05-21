<script setup lang="ts">
import { ref, useTemplateRef, onMounted } from 'vue'
import { useStationStore } from './stores/stationStore'
import { useTrainStore } from './stores/trainStore'
import { useMapStore } from './stores/mapStore'
import { useSearchStore } from './stores/searchStore'
import AppHeader from './components/layout/AppHeader.vue'
import MapContainer from './components/map/MapContainer.vue'
import StationPanel from './components/panels/StationPanel.vue'
import TrainPanel from './components/panels/TrainPanel.vue'
import TimetableModal from './components/panels/TimetableModal.vue'
import LegendPanel from './components/panels/LegendPanel.vue'
import MapControls from './components/panels/MapControls.vue'
import AgentFab from './components/agent/AgentFab.vue'
import AgentPanel from './components/agent/AgentPanel.vue'
import LoginModal from './components/auth/LoginModal.vue'
import RouteAnimationLayer from './components/map/RouteAnimationLayer.vue'
import MapAtmosphere from './components/map/MapAtmosphere.vue'
import { useAgentStore } from './stores/agentStore'
import { useUserStore } from './stores/userStore'
import { useStationSearch } from './composables/useStationSearch'
import { stationApi } from './api/stationApi'
import { trainApi } from './api/trainApi'
import { historyApi } from './api/historyApi'

// Activate search composable (starts watchers)
useStationSearch()

// Load favorites on mount if logged in
onMounted(() => { userStore.loadFavorites() })

const stationStore = useStationStore()
const trainStore = useTrainStore()
const mapStore = useMapStore()
const searchStore = useSearchStore()
const agentStore = useAgentStore()
const userStore = useUserStore()

const mapContainerRef = useTemplateRef('mapContainerRef')
const showTimetableModal = ref(false)
const showLoginModal = ref(false)
const basemapMode = ref<'maptiler-light' | 'maptiler-dark'>('maptiler-light')

// ---- Map click handlers ----
function onMapStationClick(stationId: number) {
  openStation(stationId)
}

function closeAllPanels() {
  stationStore.clear()
  trainStore.clear()
  mapStore.setFocusStation(null)
  mapStore.setFocusTrain(null)
  mapStore.setFocusCity(null)
}

// ---- Map controls ----
function handleZoomIn() {
  const mc = mapContainerRef.value as any
  if (mc?.getMap) {
    const m = mc.getMap()
    m?.zoomIn({ duration: 300 })
  }
}

function handleZoomOut() {
  const mc = mapContainerRef.value as any
  if (mc?.getMap) {
    const m = mc.getMap()
    m?.zoomOut({ duration: 300 })
  }
}

function handleLocate() {
  const mc = mapContainerRef.value as any
  if (mc?.flyTo) {
    mc.flyTo([108.0, 30.0], 4.2)
  }
}

const BASEMAP_STYLES: Record<string, string> = {
  'maptiler-light': '/map-style.json',
  'maptiler-dark': '/map-style-dark.json',
}

function handleToggleLayer() {
  const mc = mapContainerRef.value as any
  const map = mc?.getMap()
  if (!map) return

  basemapMode.value = basemapMode.value === 'maptiler-light' ? 'maptiler-dark' : 'maptiler-light'
  map.setStyle(BASEMAP_STYLES[basemapMode.value])
}

// ---- Navigation handler ----
async function handleNavigate(type: string, action: string) {
  if (type === 'station') {
    const numId = Number(action)
    if (!isNaN(numId)) {
      openStation(numId)
    } else {
      // action is a station name — search by name
      try {
        const results = await stationApi.search(action, 1)
        if (results.length > 0 && results[0].id) {
          stationStore.cacheSearchResults(results)
          openStation(results[0].id)
        }
      } catch (e) { /* ignore */ }
    }
  } else if (type === 'train') {
    openTrain(action)
  } else if (type === 'city') {
    focusCity(action)
  }
}

async function openStation(stationId: number) {
  // Always fetch detail from API (cache may have only search-level data without routes)
  let station = stationStore.getStation(stationId)
  if (!station || !station.routes) {
    try {
      station = await stationApi.getById(stationId)
      stationStore.cacheStation(station)
    } catch (e) {
      console.warn('Failed to fetch station detail', e)
      return
    }
  }
  trainStore.clear()
  mapStore.setFocusTrain(null)
  mapStore.setFocusCity(null)
  stationStore.setCurrentStation(stationId)
  mapStore.setFocusStation(String(stationId))
}

async function openTrain(trainNo: string) {
  // Fetch detail if not cached, or if cached version lacks stops (e.g. from search results)
  let train = trainStore.getTrain(trainNo)
  if (!train || !train.stops) {
    try {
      train = await trainApi.getByNo(trainNo)
      trainStore.cacheTrain(train)
    } catch (e) {
      console.warn('Failed to fetch train detail', e)
      return
    }
  }
  stationStore.clear()
  mapStore.setFocusStation(null)
  mapStore.setFocusCity(null)
  trainStore.setCurrentTrain(trainNo)
  mapStore.setFocusTrain(trainNo)
}

function focusCity(city: string) {
  stationStore.clear()
  trainStore.clear()
  mapStore.setFocusStation(null)
  mapStore.setFocusTrain(null)
  mapStore.setFocusCity(city)
}

function closeStationPanel() {
  stationStore.clear()
  mapStore.setFocusStation(null)
  mapStore.setFocusCity(null)
}

function closeTrainPanel() {
  trainStore.clear()
  mapStore.setFocusTrain(null)
  mapStore.setFocusCity(null)
}

function handleSearchSelect(item: { type: string; action: string; label?: string }) {
  // Auto-save search history
  if (userStore.isLoggedIn) {
    const q = item.label || item.action
    historyApi.add(item.type, q).catch(() => {})
  }
  if (item.type === 'station') {
    const numId = Number(item.action)
    if (!isNaN(numId)) openStation(numId)
  } else if (item.type === 'train') {
    openTrain(item.action)
  } else if (item.type === 'city') {
    focusCity(item.action)
  }
}

</script>

<template>
  <div class="app-shell">
    <AppHeader @search-select="handleSearchSelect" @show-login="showLoginModal = true" />

    <div class="map-area">
      <MapContainer
        ref="mapContainerRef"
        @station-click="onMapStationClick"
        @map-background-click="closeAllPanels"
      />

      <!-- Left panels -->
      <StationPanel
        v-if="stationStore.hasStation"
        @close="closeStationPanel"
        @navigate="handleNavigate"
        @show-all-trains="(_id) => { showTimetableModal = true }"
      />

      <TrainPanel
        v-if="trainStore.hasTrain"
        @close="closeTrainPanel"
        @navigate="handleNavigate"
      />

      <!-- Central modal -->
      <TimetableModal
        v-model:visible="showTimetableModal"
        @close="showTimetableModal = false"
        @navigate="handleNavigate"
      />

      <!-- Top-right: Legend + Map Controls -->
      <div class="top-right-group" :class="{ shifted: agentStore.isOpen }">
        <MapControls
          @zoom-in="handleZoomIn"
          @zoom-out="handleZoomOut"
          @locate="handleLocate"
          @toggle-layer="handleToggleLayer"
        />
        <LegendPanel />
      </div>

      <!-- Route animation layer -->
      <RouteAnimationLayer />

      <!-- Map atmosphere (grain + compass) -->
      <MapAtmosphere />

      <!-- Agent -->
      <AgentFab />
      <AgentPanel @navigate="handleNavigate" />

      <!-- Auth modal -->
      <LoginModal v-if="showLoginModal" @close="showLoginModal = false" />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.map-area {
  position: absolute;
  top: var(--header-h);
  left: 0;
  right: 0;
  bottom: 0;
}

.top-right-group {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  opacity: 0;
  transition: right var(--duration-slow) var(--ease-mechanical);
  animation: controls-enter var(--duration-slow) var(--ease-mechanical) forwards;
  animation-delay: 1.5s;
}

.top-right-group.shifted {
  right: 436px;
}

@keyframes controls-enter {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Responsive: Tablet ---- */
@media (max-width: 900px) {
  .top-right-group {
    top: var(--space-3);
    right: var(--space-3);
    width: 200px;
  }

  .top-right-group.shifted {
    right: calc(100vw - 48px);
  }
}

/* ---- Responsive: Mobile ---- */
@media (max-width: 640px) {
  .top-right-group {
    top: var(--space-2);
    right: var(--space-2);
    gap: var(--space-1);
    width: 180px;
  }
}
</style>
