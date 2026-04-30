<script setup lang="ts">
import { NMenu, NH3 } from 'naive-ui'
import { useRouter } from 'vue-router'

const router = useRouter()

const menuOptions = [
  { label: '地图', key: 'map' },
  { label: '换乘查询', key: 'transfer' }
]

function onMenuChange(key: string) {
  router.push({ name: key })
}
</script>

<template>
  <div class="flex items-center px-4 h-14">
    <n-h3 class="mr-6 mb-0">中国铁路地图</n-h3>
    <n-menu
      mode="horizontal"
      :options="menuOptions"
      default-value="map"
      @update:value="onMenuChange"
    />
  </div>
</template>
