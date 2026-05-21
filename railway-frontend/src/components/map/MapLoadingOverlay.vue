<script setup lang="ts">
import { computed } from 'vue'
import { useMapStore } from '../../stores/mapStore'

const mapStore = useMapStore()

const progress = computed(() => {
  if (mapStore.entryPhase === 'complete') return 100
  if (mapStore.entryPhase === 'background') return 25
  if (mapStore.entryPhase === 'lines') return 55
  if (mapStore.entryPhase === 'stations') return 80
  if (mapStore.entryPhase === 'ui') return 95
  return 0
})

const isVisible = computed(() => mapStore.entryPhase !== 'complete')
</script>

<template>
  <Transition name="loading-fade">
    <div v-if="isVisible" class="loading-overlay">
      <!-- Rail track pattern background -->
      <div class="loading-pattern" />

      <div class="loading-content">
        <!-- Signal lamp indicator -->
        <div class="signal-lamp">
          <div class="lamp-ring">
            <div class="lamp-glow" :style="{ opacity: progress / 100 }" />
          </div>
        </div>

        <!-- Progress bar styled as rail -->
        <div class="rail-progress-track">
          <div class="rail-line" />
          <div
            class="rail-progress-fill"
            :style="{ width: progress + '%' }"
          />
          <div
            class="rail-cross-tie"
            :style="{ left: progress + '%' }"
          />
        </div>

        <span class="loading-label">
          {{ progress < 30 ? '载入底图…' : progress < 60 ? '铺设线路…' : progress < 85 ? '部署信号站…' : '即将就绪' }}
        </span>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-map);
}

.loading-pattern {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px);
  background-size: 80px 80px;
}

.loading-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
}

/* Signal lamp */
.signal-lamp {
  width: 64px;
  height: 64px;
  position: relative;
}

.lamp-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid var(--signal-red);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: lamp-pulse 2s ease-in-out infinite;
}

.lamp-glow {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--signal-red);
  box-shadow: 0 0 20px var(--signal-red);
  transition: opacity var(--duration-slow) var(--ease-signal);
}

@keyframes lamp-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(214, 48, 49, 0.3); }
  50% { box-shadow: 0 0 0 12px rgba(214, 48, 49, 0); }
}

/* Rail progress track */
.rail-progress-track {
  width: 240px;
  height: 18px;
  position: relative;
  display: flex;
  align-items: center;
}

.rail-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 2px;
  background: var(--border-medium);
}

.rail-progress-fill {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 3px;
  background: var(--signal-red);
  border-radius: 1px;
  transition: width var(--duration-normal) var(--ease-mechanical);
}

.rail-cross-tie {
  position: absolute;
  top: 0;
  width: 4px;
  height: 18px;
  background: var(--signal-red);
  border-radius: 1px;
  transform: translateX(-2px);
  transition: left var(--duration-normal) var(--ease-mechanical);
}

.loading-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  letter-spacing: 2px;
  text-transform: uppercase;
}

/* Exit transition */
.loading-fade-leave-active {
  transition: opacity 0.5s var(--ease-mechanical);
}
.loading-fade-leave-to {
  opacity: 0;
}
</style>
