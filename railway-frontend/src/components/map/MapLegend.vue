<script setup lang="ts">
import { ref, watch } from 'vue'
import { NCollapse, NCollapseItem, NCheckbox, NSpace, NSwitch } from 'naive-ui'
import { useMapStore } from '../../stores/mapStore'

const mapStore = useMapStore()

const railwaysVisible = ref(true)
const stationsVisible = ref(true)

watch(railwaysVisible, (v) => {
  mapStore.layerVisibility.railways = v
  // 通过 MapLibre 控制图层可见性
  // map?.setLayoutProperty('railways-layer', 'visibility', v ? 'visible' : 'none')
})
watch(stationsVisible, (v) => {
  mapStore.layerVisibility.stations = v
})

const railwayCategories = [
  { code: 'high_speed', label: '高速铁路', color: '#ff481a', width: 3 },
  { code: 'rapid_transit', label: '快速铁路/城际', color: '#ffa31a', width: 2.5 },
  { code: 'conventional', label: '普通铁路', color: '#e74c3c', width: 2 },
  { code: 'passenger_rail', label: '客运专线', color: '#6ed568', width: 2 },
  { code: 'freight_rail', label: '货运专线', color: '#d3ff4f', width: 2 },
  { code: 'other_rail', label: '专用线/联络线', color: '#708bbb', width: 1.5, dashed: true },
  { code: 'subway', label: '地铁', color: '#85C1E9', width: 1.5 },
]

const stationCategories = [
  { code: 'major_hub', label: '重要枢纽', color: '#e74c3c', size: 8 },
  { code: 'major_passenger', label: '主要车站', color: '#e74c3c', size: 7 },
  { code: 'medium_passenger', label: '中等车站', color: '#f39c12', size: 5 },
  { code: 'small_passenger', label: '小型车站', color: '#f39c12', size: 4 },
  { code: 'large_yard', label: '大型编组站', color: '#3498db', size: 6 },
  { code: 'medium_yard', label: '中小编组站', color: '#3498db', size: 4 },
  { code: 'major_freight', label: '重要货运站', color: '#8B4513', size: 6 },
  { code: 'signal_station', label: '线路所/信号站', color: '#27ae60', size: 3 },
  { code: 'emu_depot', label: '动车整备场', color: '#9b59b6', size: 4 },
]
</script>

<template>
  <div class="map-legend min-w-[220px]">
    <n-collapse default-expanded-names="railways">
      <n-collapse-item title="铁路线图例" name="railways">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-gray-500">显示铁路线</span>
          <n-switch v-model:value="railwaysVisible" size="small" />
        </div>
        <n-space vertical :size="3">
          <div
            v-for="c in railwayCategories" :key="c.code"
            class="flex items-center gap-2 text-xs py-0.5"
          >
            <span
              class="inline-block rounded"
              :style="{
                width: '24px',
                height: `${c.width}px`,
                background: c.color,
                borderTop: c.dashed ? '1px dashed ' + c.color : undefined
              }"
            />
            <span class="text-gray-700">{{ c.label }}</span>
          </div>
        </n-space>
      </n-collapse-item>
      <n-collapse-item title="车站图例" name="stations">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-gray-500">显示车站</span>
          <n-switch v-model:value="stationsVisible" size="small" />
        </div>
        <n-space vertical :size="3">
          <div
            v-for="c in stationCategories" :key="c.code"
            class="flex items-center gap-2 text-xs py-0.5"
          >
            <span
              class="inline-block rounded-full border border-white"
              :style="{
                width: `${c.size}px`,
                height: `${c.size}px`,
                background: c.color,
              }"
            />
            <span class="text-gray-700">{{ c.label }}</span>
          </div>
        </n-space>
      </n-collapse-item>
    </n-collapse>
  </div>
</template>
