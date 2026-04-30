<script setup lang="ts">
import { NTabs, NTabPane } from 'naive-ui'
import { useSearchStore } from '../../stores/searchStore'
import StationSearch from './StationSearch.vue'
import TrainSearch from './TrainSearch.vue'

const searchStore = useSearchStore()
</script>

<template>
  <div class="search-panel">
    <div class="bg-white/95 rounded-lg shadow-lg p-3">
      <n-tabs v-model:value="searchStore.activeTab" type="line" size="small">
        <n-tab-pane name="station" tab="车站">
          <StationSearch />
        </n-tab-pane>
        <n-tab-pane name="train" tab="车次">
          <TrainSearch />
        </n-tab-pane>
        <n-tab-pane name="transfer" tab="换乘">
          <div class="text-sm text-gray-500 p-2">
            请使用<a href="/transfer" class="text-blue-500">换乘查询</a>页面
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>
  </div>
</template>
