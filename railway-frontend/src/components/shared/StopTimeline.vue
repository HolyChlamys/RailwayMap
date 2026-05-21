<script setup lang="ts">
import type { TrainStop } from '../../types/train'
import HyperlinkText from './HyperlinkText.vue'

defineProps<{
  stops: TrainStop[]
}>()

const emit = defineEmits<{
  navigate: [type: string, action: string]
}>()

function dwellLabel(minutes: number): string {
  if (minutes <= 0) return ''
  return `停${minutes}分`
}
</script>

<template>
  <div class="timeline">
    <div class="timeline-track" />
    <div
      v-for="(stop, i) in stops"
      :key="i"
      class="stop-item"
      :class="{ terminal: i === 0 || i === stops.length - 1 }"
    >
      <!-- Time column -->
      <div class="stop-time-col">
        <span v-if="stop.arrive !== '-'" class="stop-time">{{ stop.arrive }}</span>
        <span v-else class="stop-time-label">始发</span>
        <span class="stop-time-sep">—</span>
        <span v-if="stop.depart !== '-'" class="stop-time">{{ stop.depart }}</span>
        <span v-else class="stop-time-label">终到</span>
      </div>

      <!-- Station name -->
      <div class="stop-station-col">
        <HyperlinkText
          type="station"
          :action="stop.station"
          :label="stop.station"
          @navigate="(t, a) => emit('navigate', t, a)"
        />
      </div>

      <!-- Dwell info -->
      <div class="stop-dwell-col">
        <span v-if="stop.dwellMinutes > 0" class="stop-dwell">
          {{ dwellLabel(stop.dwellMinutes) }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  position: relative;
  padding-left: 12px;
}

.timeline-track {
  position: absolute;
  left: 4px;
  top: 12px;
  bottom: 12px;
  width: 2px;
  background: var(--border-medium);
  border-radius: 1px;
}

.stop-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  position: relative;
}

/* Timeline dot */
.stop-item::before {
  content: '';
  position: absolute;
  left: -11px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid var(--signal-red);
  background: var(--glass-bg-active);
  z-index: 1;
}

.stop-item.terminal::before {
  background: var(--signal-red);
}

/* Time column */
.stop-time-col {
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 100px;
  flex-shrink: 0;
}

.stop-time {
  font-family: var(--font-mono);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
}

.stop-time-sep {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0 1px;
}

.stop-time-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: 500;
  width: 40px;
  text-align: center;
}

/* Station column */
.stop-station-col {
  flex: 1;
  min-width: 0;
}

/* Dwell column */
.stop-dwell-col {
  flex-shrink: 0;
  min-width: 40px;
  text-align: right;
}

.stop-dwell {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
</style>
