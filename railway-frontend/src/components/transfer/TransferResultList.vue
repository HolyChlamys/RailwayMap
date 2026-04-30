<script setup lang="ts">
import type { TransferResult } from '../../types/transfer'
import { NCard, NTag, NSpace } from 'naive-ui'

defineProps<{ results: TransferResult[] }>()
const emit = defineEmits<{ select: [TransferResult] }>()
</script>

<template>
  <n-space vertical>
    <n-card
      v-for="r in results" :key="r.id"
      size="small" hoverable
      @click="emit('select', r)"
    >
      <div class="flex justify-between items-center">
        <div>
          <n-tag type="info" size="small">{{ r.transferCount }}次换乘</n-tag>
          <span class="ml-2 font-medium">{{ Math.floor(r.totalTimeMin / 60) }}h{{ r.totalTimeMin % 60 }}m</span>
        </div>
        <span class="text-orange-500 font-bold">¥{{ r.totalPriceYuan }}</span>
      </div>
      <div class="text-xs text-gray-400 mt-1">
        {{ r.segments.map(s => s.trainNo).join(' → ') }}
      </div>
    </n-card>
    <div v-if="results.length === 0" class="text-gray-400 text-center text-sm">
      暂无结果
    </div>
  </n-space>
</template>
