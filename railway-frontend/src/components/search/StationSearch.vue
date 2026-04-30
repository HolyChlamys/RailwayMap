<script setup lang="ts">
import { ref } from 'vue'
import { NAutoComplete, NTag, NSpace } from 'naive-ui'
import { searchStations } from '../../services/stationService'
import { useMapStore } from '../../stores/mapStore'
import type { StationSearchResult } from '../../types/station'

const mapStore = useMapStore()
const query = ref('')
const options = ref<{ label: string; value: string; station: StationSearchResult }[]>([])
const loading = ref(false)

const categoryColors: Record<string, string> = {
  major_hub: 'error',
  major_passenger: 'error',
  medium_passenger: 'warning',
  small_passenger: 'warning',
  large_yard: 'info',
  medium_yard: 'info',
  major_freight: 'default',
  signal_station: 'success'
}

async function onSearch(q: string) {
  if (q.length < 1) {
    options.value = []
    return
  }
  loading.value = true
  try {
    const res = await searchStations(q)
    options.value = res.data.map(s => ({
      label: `${s.name} — ${s.city}`,
      value: s.name,
      station: s
    }))
  } finally {
    loading.value = false
  }
}

function onSelect(_val: string, opt: (typeof options.value)[0]) {
  if (opt?.station) {
    mapStore.setCenter(opt.station.lon, opt.station.lat)
    mapStore.setZoom(14)
    mapStore.selectStation(opt.station.id)
  }
}

function getCategoryLabel(cat: string) {
  const map: Record<string, string> = {
    major_hub: '枢纽', major_passenger: '主要站', medium_passenger: '中等站',
    small_passenger: '小型站', large_yard: '编组站', signal_station: '线路所'
  }
  return map[cat] || cat
}
</script>

<template>
  <div class="py-2">
    <n-auto-complete
      v-model:value="query"
      :options="options"
      :loading="loading"
      placeholder="搜索车站（中文/拼音/首字母）"
      :get-show="() => true"
      @update:value="onSearch"
      @select="onSelect"
      clearable
    />
  </div>
</template>
