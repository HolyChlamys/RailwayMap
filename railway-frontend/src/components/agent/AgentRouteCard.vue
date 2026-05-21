<script setup lang="ts">
import type { RoutePlan } from '../../types/route'

defineProps<{
  plan: RoutePlan
}>()

const emit = defineEmits<{
  navigate: [type: string, action: string]
}>()
</script>

<template>
  <div class="route-card">
    <div class="route-card-header" :style="{ color: plan.color }">
      <span class="route-dot" :style="{ background: plan.color }" />
      {{ plan.label }}
    </div>
    <div class="route-card-segments">
      <div
        v-for="(seg, i) in plan.segments"
        :key="i"
        class="route-seg-row"
      >
        <template v-if="seg.trainNo">
          <span class="seg-dot" :style="{ background: plan.color }" />
          <span class="seg-station">{{ seg.from }}</span>
          <span class="seg-train">—<b>{{ seg.trainNo }}</b>→</span>
          <span class="seg-station">{{ seg.to }}</span>
          <span class="seg-time">{{ seg.depart }}—{{ seg.arrive }}</span>
        </template>
        <template v-else>
          <span class="seg-transfer">↳ 换乘</span>
        </template>
      </div>
    </div>
    <div class="route-card-meta">
      ⏱ {{ Math.floor(plan.totalDurationMin / 60) }}h{{ plan.totalDurationMin % 60 }}min · 🔄 {{ plan.transfers }} 次换乘
    </div>
  </div>
</template>

<style scoped>
.route-card {
  background: var(--glass-bg-active);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  margin-top: var(--space-2);
  border: 1px solid var(--border-light);
}

.route-card-header {
  font-weight: 700;
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.route-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.route-seg-row {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px 0;
  font-size: var(--text-sm);
}

.seg-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.seg-station {
  font-size: var(--text-sm);
}

.seg-train {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.seg-train b {
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.seg-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-left: auto;
}

.seg-transfer {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  padding-left: 12px;
}

.route-card-meta {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-1);
}
</style>
