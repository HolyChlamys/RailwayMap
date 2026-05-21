<script setup lang="ts">
import type { TrainType } from '../../types/train'
import { TRAIN_TYPE_INFO } from '../../types/train'

const props = defineProps<{
  type: TrainType
  size?: 'sm' | 'md'
}>()

const info = TRAIN_TYPE_INFO[props.type] ?? TRAIN_TYPE_INFO.K
const tagSize = props.size === 'sm' ? 'tag-sm' : 'tag-md'
</script>

<template>
  <span
    class="train-tag"
    :class="tagSize"
    :style="{ background: info.color }"
  >
    {{ type }}
  </span>
</template>

<style scoped>
.train-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-weight: 700;
  color: white;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.tag-sm {
  width: 22px;
  height: 18px;
  font-size: var(--text-2xs);
}

.tag-md {
  width: 28px;
  height: 22px;
  font-size: var(--text-xs);
}
</style>
