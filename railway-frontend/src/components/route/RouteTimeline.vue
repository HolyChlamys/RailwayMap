<script setup lang="ts">
import type { TrainStopInfo } from '../../types/train'
import { NTimeline, NTimelineItem } from 'naive-ui'

defineProps<{ stops: TrainStopInfo[] }>()
</script>

<template>
  <div class="route-timeline">
    <n-timeline>
      <n-timeline-item
        v-for="stop in stops"
        :key="stop.seq"
        :title="stop.stationName"
        :time="stop.departTime || stop.arriveTime"
        :content="`停站 ${stop.stayMin || 0} 分钟`"
      />
    </n-timeline>
  </div>
</template>
