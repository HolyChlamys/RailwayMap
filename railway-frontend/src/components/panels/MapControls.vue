<script setup lang="ts">
import { useMapStore } from '../../stores/mapStore'

const mapStore = useMapStore()

defineEmits<{
  zoomIn: []
  zoomOut: []
  locate: []
  toggleLayer: []
}>()
</script>

<template>
  <div class="map-controls">
    <button
      class="ctrl-btn"
      title="放大"
      @click="$emit('zoomIn')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    </button>

    <button
      class="ctrl-btn"
      title="缩小"
      @click="$emit('zoomOut')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    </button>

    <button
      class="ctrl-btn"
      title="定位"
      @click="$emit('locate')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
      </svg>
    </button>

    <button
      class="ctrl-btn"
      title="图层"
      @click="$emit('toggleLayer')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.map-controls {
  display: flex;
  gap: var(--space-2);
  width: 240px;
}

.ctrl-btn {
  flex: 1;
  height: 38px;
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm);
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast) var(--ease-signal);
  color: var(--text-secondary);
}

.ctrl-btn:hover {
  background: var(--glass-bg-hover);
  box-shadow: var(--shadow-md);
  color: var(--text-primary);
}

.ctrl-btn:active {
  transform: scale(0.95);
}

.ctrl-btn svg {
  width: 18px;
  height: 18px;
}
</style>
