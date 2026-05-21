<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTrainStore } from '../../stores/trainStore'
import { useUserStore } from '../../stores/userStore'
import { TRAIN_TYPE_INFO } from '../../types/train'
import GlassCard from '../shared/GlassCard.vue'
import TrainTypeTag from '../shared/TrainTypeTag.vue'
import HyperlinkText from '../shared/HyperlinkText.vue'
import StopTimeline from '../shared/StopTimeline.vue'

const MAX_VISIBLE_STOPS = 6

const trainStore = useTrainStore()
const userStore = useUserStore()
const showAllStops = ref(false)

const emit = defineEmits<{
  close: []
  navigate: [type: string, action: string]
}>()

const train = computed(() => trainStore.currentTrain)
const typeInfo = computed(() => train.value ? TRAIN_TYPE_INFO[train.value.type] : null)

const visibleStops = computed(() => {
  const stops = train.value?.stops
  if (!stops || stops.length === 0) return []
  if (showAllStops.value || stops.length <= MAX_VISIBLE_STOPS) return stops
  return stops.slice(0, MAX_VISIBLE_STOPS)
})

const hiddenStopCount = computed(() => {
  const stops = train.value?.stops
  if (!stops || stops.length <= MAX_VISIBLE_STOPS) return 0
  return stops.length - MAX_VISIBLE_STOPS
})

const durationLabel = computed(() => {
  if (!train.value) return ''
  const dur = train.value.durationMin
  if (!dur || dur <= 0) return ''
  const h = Math.floor(dur / 60)
  const m = dur % 60
  return `${h} 小时 ${m > 0 ? m + ' 分钟' : ''}`
})
</script>

<template>
  <Transition name="panel-slide">
    <div v-if="train" class="train-panel">
      <GlassCard>
        <!-- Header -->
        <template #header>
          <div class="panel-header">
            <div class="panel-icon train-icon">
              {{ train.type }}
            </div>
            <div class="panel-title-group">
              <div class="panel-title-row">
                <h2 class="panel-title">{{ train.no }}</h2>
                <TrainTypeTag :type="train.type" size="sm" />
              </div>
              <p class="panel-subtitle">
                {{ train.from }} → {{ train.to }}
              </p>
            </div>
            <button
              v-if="userStore.isLoggedIn"
              class="panel-fav"
              :class="{ favorited: userStore.isFavorite('train', train.no) }"
              :title="userStore.isFavorite('train', train.no) ? '取消收藏' : '收藏'"
              @click="userStore.toggleFavorite('train', train.no, train.no, { from: train.from, to: train.to, type: train.type })"
            >
              {{ userStore.isFavorite('train', train.no) ? '★' : '☆' }}
            </button>
            <button class="panel-close" @click="emit('close')" title="关闭">
              ✕
            </button>
          </div>
        </template>

        <!-- Tags -->
        <div class="panel-tags">
          <span class="panel-tag tag-major">{{ train.type }}字头</span>
          <span v-if="typeInfo" class="panel-tag tag-passenger">
            {{ typeInfo.label }}
          </span>
        </div>

        <!-- Origin / Destination -->
        <div class="panel-row">
          <span class="panel-label">始发站</span>
          <span class="panel-value">
            <HyperlinkText
              type="station"
              :action="train.from"
              @navigate="(t, a) => emit('navigate', t, a)"
            />
          </span>
        </div>

        <div class="panel-row">
          <span class="panel-label">终到站</span>
          <span class="panel-value">
            <HyperlinkText
              type="station"
              :action="train.to"
              @navigate="(t, a) => emit('navigate', t, a)"
            />
          </span>
        </div>

        <div class="panel-row">
          <span class="panel-label">运行时间</span>
          <span class="panel-value">
            <span class="time-badge">{{ train.departTime }}</span>
            <span class="time-arrow">→</span>
            <span class="time-badge">{{ train.arriveTime }}</span>
            <span class="time-duration">{{ durationLabel }}</span>
          </span>
        </div>

        <!-- Stop timeline -->
        <div class="panel-section-label">
          经停站 ({{ train.stops?.length ?? 0 }})
        </div>
        <div class="stops-scroll">
          <StopTimeline
            :stops="visibleStops"
            @navigate="(t, a) => emit('navigate', t, a)"
          />
          <button
            v-if="hiddenStopCount > 0 && !showAllStops"
            class="btn-expand-stops"
            @click="showAllStops = true"
          >
            展开全部 {{ hiddenStopCount }} 站
          </button>
          <button
            v-if="showAllStops && train.stops && train.stops.length > MAX_VISIBLE_STOPS"
            class="btn-expand-stops"
            @click="showAllStops = false"
          >
            收起
          </button>
        </div>
      </GlassCard>
    </div>
  </Transition>
</template>

<style scoped>
.train-panel {
  position: absolute;
  top: calc(var(--header-h) + var(--space-4));
  left: var(--space-4);
  z-index: 200;
  width: 360px;
  max-height: calc(100vh - var(--header-h) - var(--space-8));
  overflow-y: auto;
}

/* Header */
.panel-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.panel-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: var(--text-lg);
  flex-shrink: 0;
  box-shadow: var(--shadow-signal);
}

.train-icon {
  background: var(--signal-amber);
}

.panel-title-group {
  flex: 1;
  min-width: 0;
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.panel-title {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
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

/* Tags */
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
  background: rgba(225, 112, 85, 0.10);
  color: var(--signal-amber);
}

.tag-passenger {
  background: rgba(0, 184, 148, 0.10);
  color: var(--signal-green);
}

/* Info rows */
.panel-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-1) 0;
}

.panel-label {
  color: var(--text-tertiary);
  min-width: 56px;
  flex-shrink: 0;
  font-size: var(--text-sm);
  padding-top: 1px;
}

.panel-value {
  color: var(--text-primary);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.time-badge {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--text-primary);
}

.time-arrow {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.time-duration {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* Section label */
.panel-section-label {
  font-family: var(--font-mono);
  font-size: var(--text-2xs);
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin: var(--space-4) 0 var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-light);
}

.stops-scroll {
  max-height: 280px;
  overflow-y: auto;
}

.btn-expand-stops {
  width: 100%;
  padding: 6px var(--space-3);
  margin-top: var(--space-2);
  border: 1px dashed var(--border-medium);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.btn-expand-stops:hover {
  border-color: var(--signal-blue);
  color: var(--signal-blue);
}

/* Transitions */
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
  .train-panel {
    left: var(--space-2);
    top: calc(var(--header-h) + var(--space-2));
    width: calc(100vw - 16px);
    max-height: 50vh;
  }
}
</style>
