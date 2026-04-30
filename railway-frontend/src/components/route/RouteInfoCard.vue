<script setup lang="ts">
import type { TrainRouteDetail } from '../../types/train'
import { NCard, NTag, NSpace, NDescriptions, NDescriptionsItem } from 'naive-ui'

defineProps<{ detail: TrainRouteDetail }>()
</script>

<template>
  <n-card size="small" :title="`${detail.trainNo} (${detail.trainType}字头)`">
    <n-descriptions :column="2" size="small" bordered>
      <n-descriptions-item label="始发站">{{ detail.departStation }}</n-descriptions-item>
      <n-descriptions-item label="终到站">{{ detail.arriveStation }}</n-descriptions-item>
      <n-descriptions-item label="发车">{{ detail.departTime }}</n-descriptions-item>
      <n-descriptions-item label="到达">{{ detail.arriveTime }}</n-descriptions-item>
      <n-descriptions-item label="全程耗时">{{ detail.durationMin }} 分钟</n-descriptions-item>
      <n-descriptions-item label="途经站数">{{ detail.stops.length }}</n-descriptions-item>
    </n-descriptions>
  </n-card>
</template>
