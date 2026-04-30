<script setup lang="ts">
import { ref } from 'vue'
import { NAutoComplete } from 'naive-ui'
import { searchTrains, getTrainRoute } from '../../services/trainService'
import { useMapStore } from '../../stores/mapStore'
import type { TrainSearchResult } from '../../types/train'

const mapStore = useMapStore()
const query = ref('')
const options = ref<{ label: string; value: string; train: TrainSearchResult }[]>([])
const loading = ref(false)

async function onSearch(q: string) {
  if (q.length < 1) {
    options.value = []
    return
  }
  if (/^[GCDZTKYSgcdztkys]\d*$/.test(q.trim())) {
    loading.value = true
    try {
      const res = await searchTrains(q)
      options.value = res.data.map(t => ({
        label: `${t.trainNo} ${t.departStation}-${t.arriveStation}`,
        value: t.trainNo,
        train: t
      }))
    } finally {
      loading.value = false
    }
  }
}

async function onSelect(_val: string, opt: (typeof options.value)[0]) {
  if (opt?.train) {
    mapStore.highlightTrain(opt.train.trainNo)
    try {
      const res = await getTrainRoute(opt.train.trainNo)
      if (res.data.segmentsGeoJson) {
        mapStore.routeGeoJson = res.data.segmentsGeoJson
      }
    } catch {
      // 路线数据暂不可用
    }
  }
}
</script>

<template>
  <div class="py-2">
    <n-auto-complete
      v-model:value="query"
      :options="options"
      :loading="loading"
      placeholder="搜索车次（如 G1、D301）"
      :get-show="() => true"
      @update:value="onSearch"
      @select="onSelect"
      clearable
    />
  </div>
</template>
