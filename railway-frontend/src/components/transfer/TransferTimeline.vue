<script setup lang="ts">
import type { TransferResult } from '../../types/transfer'
import { NTimeline, NTimelineItem, NTag, NCard } from 'naive-ui'

defineProps<{ result: TransferResult }>()
</script>

<template>
  <n-card :title="`${result.transferCount}次换乘 · 总计 ${Math.floor(result.totalTimeMin / 60)}h${result.totalTimeMin % 60}m · ¥${result.totalPriceYuan}`">
    <n-timeline>
      <n-timeline-item
        v-for="(seg, i) in result.segments"
        :key="i"
        :title="`${seg.trainNo} (${seg.trainType}字头)`"
        :time="`${seg.departTime} → ${seg.arriveTime}`"
      >
        <div>{{ seg.fromStation }} → {{ seg.toStation }}</div>
        <div class="text-sm text-gray-500">
          耗时 {{ Math.floor(seg.durationMin / 60) }}h{{ seg.durationMin % 60 }}m
           · 二等座 ¥{{ seg.price?.second }}
        </div>
      </n-timeline-item>
    </n-timeline>
  </n-card>
</template>
