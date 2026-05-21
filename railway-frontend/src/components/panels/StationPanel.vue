<script setup lang="ts">
import { computed, watch, onMounted } from 'vue'
import { useStationStore } from '../../stores/stationStore'
import { useTrainStore } from '../../stores/trainStore'
import { useUserStore } from '../../stores/userStore'
import { STATION_TYPE_LABELS } from '../../types/station'
import GlassCard from '../shared/GlassCard.vue'
import HyperlinkText from '../shared/HyperlinkText.vue'

const stationStore = useStationStore()
const trainStore = useTrainStore()
const userStore = useUserStore()

const emit = defineEmits<{
  close: []
  navigate: [type: string, action: string]
  showAllTrains: [stationId: number]
}>()

const station = computed(() => stationStore.currentStation)

const routeCount = computed(() => station.value?.routes?.length ?? 0)

function getRouteNames(): string {
  const s = station.value
  if (!s || !s.routes) return '暂无数据'
  const routes = s.routes
  const shown = routes.slice(0, 4).join('、')
  return shown + (routes.length > 4 ? ` 等 ${routes.length} 趟` : '')
}
</script>

<template>
  <Transition name="panel-slide">
    <div v-if="station" class="station-panel">
      <GlassCard>
        <template #header>
          <div class="panel-header">
            <div class="panel-icon station-icon">
              {{ station.name.charAt(0) }}
            </div>
            <div class="panel-title-group">
              <h2 class="panel-title">{{ station.name }}</h2>
              <p class="panel-subtitle">
                {{ station.city }} · {{ STATION_TYPE_LABELS[station.category] }}
              </p>
            </div>
            <button
              v-if="userStore.isLoggedIn"
              class="panel-fav"
              :class="{ favorited: userStore.isFavorite('station', String(station.id)) }"
              :title="userStore.isFavorite('station', String(station.id)) ? '取消收藏' : '收藏'"
              @click="userStore.toggleFavorite('station', String(station.id), station.name, { city: station.city, category: station.category })"
            >
              {{ userStore.isFavorite('station', String(station.id)) ? '★' : '☆' }}
            </button>
            <button class="panel-close" @click="emit('close')" title="关闭">
              ✕
            </button>
          </div>
        </template>

        <div class="panel-tags">
          <span class="panel-tag tag-major">
            {{ STATION_TYPE_LABELS[station.category] }}
          </span>
          <span class="panel-tag tag-passenger">客运</span>
        </div>

        <div class="panel-row">
          <span class="panel-label">所属城市</span>
          <span class="panel-value">
            <HyperlinkText
              type="city"
              :action="station.city"
              :label="station.city"
              @navigate="(t, a) => emit('navigate', t, a)"
            />
          </span>
        </div>

        <div class="panel-row">
          <span class="panel-label">途经车次</span>
          <span class="panel-value">{{ getRouteNames() }}</span>
        </div>

        <div class="panel-actions">
          <button
            class="btn-all-trains"
            @click="emit('showAllTrains', station.id)"
          >
            所有车次 ({{ routeCount }})
          </button>
        </div>
      </GlassCard>
    </div>
  </Transition>
</template>

<style scoped>
.station-panel {
  position: absolute;
  top: calc(var(--header-h) + var(--space-4));
  left: var(--space-4);
  z-index: 200;
  width: 340px;
  max-height: calc(100vh - var(--header-h) - var(--space-8));
}

.panel-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.panel-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: var(--text-lg);
  flex-shrink: 0;
  box-shadow: var(--shadow-signal);
}

.station-icon {
  background: var(--signal-red);
}

.panel-title-group {
  flex: 1;
  min-width: 0;
}

.panel-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.panel-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-top: 2px;
}

.panel-fav {
  width: 28px;
  height: 28px;
  border: none;
  background: var(--border-light);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: all var(--duration-fast);
}
.panel-fav:hover { background: var(--border-medium); }
.panel-fav.favorited {
  color: var(--signal-amber);
  background: rgba(253, 203, 110, 0.15);
}

.panel-close {
  width: 28px;
  height: 28px;
  border: none;
  background: var(--border-light);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: all var(--duration-fast);
}
.panel-close:hover {
  background: var(--border-medium);
  color: var(--text-primary);
}

.panel-tags {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin: var(--space-3) 0;
}

.panel-tag {
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
}

.tag-major {
  background: rgba(214, 48, 49, 0.10);
  color: var(--signal-red);
}

.tag-passenger {
  background: rgba(0, 184, 148, 0.10);
  color: var(--signal-green);
}

.panel-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-1) 0;
}

.panel-label {
  color: var(--text-tertiary);
  min-width: 64px;
  flex-shrink: 0;
  font-size: var(--text-sm);
  padding-top: 1px;
}

.panel-value {
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.5;
}

.panel-actions {
  padding-top: var(--space-4);
}

.btn-all-trains {
  width: 100%;
  padding: 10px var(--space-4);
  border: none;
  border-radius: var(--radius-md);
  background: var(--border-light);
  color: var(--text-primary);
  font-size: var(--font-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-signal);
  font-family: inherit;
}
.btn-all-trains:hover {
  background: var(--border-medium);
}
.btn-all-trains:active {
  transform: scale(0.98);
}

.panel-slide-enter-active {
  transition: all var(--duration-normal) var(--ease-mechanical);
}
.panel-slide-leave-active {
  transition: all 180ms var(--ease-mechanical);
}
.panel-slide-enter-from {
  opacity: 0;
  transform: translateX(-24px);
}
.panel-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

@media (max-width: 640px) {
  .station-panel {
    left: var(--space-2);
    top: calc(var(--header-h) + var(--space-2));
    width: calc(100vw - 16px);
    max-height: 45vh;
  }
}
</style>
