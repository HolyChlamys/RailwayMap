<script setup lang="ts">
import { ref } from 'vue'
import { useMapStore } from '../../stores/mapStore'

const mapStore = useMapStore()
const isCollapsed = ref(false)

const stationTypes = [
  { key: 'major_hub', label: '重要枢纽', sym: '★', color: '#d63031' },
  { key: 'major_passenger', label: '主要客运站', sym: '●', color: '#0066ff' },
  { key: 'medium_passenger', label: '中等客运站', sym: '●', color: '#0066ff' },
  { key: 'small_passenger', label: '小型客运站', sym: '●', color: '#3388ff' },
]

const lineTypes = [
  { key: 'trunk_hs', label: '高速铁路', color: '#ff3300', weight: 3, weight2: 1.5, double: true },
  { key: 'trunk_cv', label: '普速铁路', color: '#33a02c', weight: 2.5, weight2: 1.2, double: true },
  { key: 'branch', label: '支线 / 联络线', color: '#6464b5', weight: 1.5, weight2: 0, double: false },
  { key: 'spur', label: '专用线', color: '#6464b5', weight: 0.8, weight2: 0, double: false },
]
</script>

<template>
  <div class="legend-panel" :class="{ collapsed: isCollapsed }">
    <div class="legend-header" @click="isCollapsed = !isCollapsed">
      <span class="legend-header-text">图例</span>
      <button class="legend-toggle" :class="{ rotated: isCollapsed }">▼</button>
    </div>

    <div class="legend-body">
      <!-- Stations -->
      <div class="legend-section-title">车站</div>
      <div
        v-for="st in stationTypes"
        :key="st.key"
        class="legend-item legend-item-static"
      >
        <span class="sym" :style="{ color: st.color }">{{ st.sym }}</span>
        <span class="lbl">{{ st.label }}</span>
      </div>

      <hr class="legend-divider">

      <!-- Lines -->
      <div class="legend-section-title">铁路（双线 / 单线）</div>
      <label
        v-for="lt in lineTypes"
        :key="lt.key"
        class="legend-item"
      >
        <input
          type="checkbox"
          :checked="mapStore.layerVisibility.lines[lt.key] ?? true"
          @change="mapStore.toggleLineType(lt.key)"
        />
        <span class="sym">
          <svg width="40" height="12" class="line-preview">
            <!-- Double line: two parallel lines -->
            <template v-if="lt.double">
              <line x1="0" y1="3" x2="40" y2="3"
                :stroke="lt.color" :stroke-width="lt.weight" stroke-linecap="round" />
              <line x1="0" y1="9" x2="40" y2="9"
                :stroke="lt.color" :stroke-width="lt.weight2" stroke-linecap="round" opacity="0.6" />
            </template>
            <!-- Single line: one dashed line -->
            <template v-else>
              <line x1="0" y1="6" x2="40" y2="6"
                :stroke="lt.color" :stroke-width="lt.weight" stroke-linecap="round"
                :stroke-dasharray="lt.weight2 === 0 ? '6,4' : 'none'" />
            </template>
          </svg>
        </span>
        <span class="lbl">{{ lt.label }}</span>
      </label>
    </div>
  </div>
</template>

<style scoped>
.legend-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  width: 240px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
  transition: max-height var(--duration-slow) var(--ease-mechanical);
  overflow: hidden;
}

.legend-panel.collapsed {
  max-height: 40px;
}

/* Header */
.legend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px var(--space-4);
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;
}

.legend-header:hover {
  background: var(--border-light);
}

.legend-header-text {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
}

.legend-toggle {
  width: 22px;
  height: 22px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: 11px;
  transition: transform var(--duration-normal) var(--ease-signal);
}

.legend-toggle.rotated {
  transform: rotate(-90deg);
}

/* Body */
.legend-body {
  overflow-y: auto;
  flex: 1;
  padding: 0 var(--space-4) var(--space-4);
  transition: opacity var(--duration-normal);
}

.legend-panel.collapsed .legend-body {
  opacity: 0;
  pointer-events: none;
}

/* Section titles */
.legend-section-title {
  font-family: var(--font-mono);
  font-size: var(--text-2xs);
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: var(--space-2) 0;
  margin-top: var(--space-2);
  border-bottom: 1px solid var(--border-light);
}

/* Divider */
.legend-divider {
  border: none;
  border-top: 1px solid var(--border-light);
  margin: var(--space-2) 0 0 0;
}

/* Items */
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 4px var(--space-1);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-xs);
  transition: background var(--duration-instant);
}

.legend-item-static {
  cursor: default;
}

.legend-item-static:hover {
  background: transparent;
}

.legend-item:hover {
  background: var(--border-light);
}

.legend-item input[type="checkbox"] {
  width: 13px;
  height: 13px;
  accent-color: var(--text-secondary);
  cursor: pointer;
}

.sym {
  width: 42px;
  height: 18px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.line-preview {
  display: block;
  overflow: visible;
}

.lbl {
  flex: 1;
  color: var(--text-secondary);
}
</style>
