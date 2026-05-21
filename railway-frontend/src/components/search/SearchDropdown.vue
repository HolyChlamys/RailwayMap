<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore, type SearchResultItem } from '../../stores/searchStore'
import TrainTypeTag from '../shared/TrainTypeTag.vue'
import type { TrainType } from '../../types/train'
import { STATION_TYPE_LABELS } from '../../types/station'

const searchStore = useSearchStore()

defineEmits<{
  select: [item: SearchResultItem]
}>()

const sectionTitle = computed(() => {
  if (searchStore.query) {
    const map: Record<string, string> = { station: '车站', train: '车次', city: '城市' }
    return map[searchStore.activeTab] ?? ''
  }
  const map: Record<string, string> = { station: '热门车站', train: '热门车次', city: '热门城市' }
  return map[searchStore.activeTab] ?? ''
})

function getStationDotColor(type: string): string {
  if (type === 'major_hub') return 'var(--signal-red)'
  if (type.includes('passenger')) return 'var(--signal-amber)'
  return 'var(--text-tertiary)'
}
</script>

<template>
  <div v-if="searchStore.results.length > 0" class="dropdown">
    <div class="dropdown-section-title">{{ sectionTitle }}</div>
    <div
      v-for="item in searchStore.results"
      :key="item.action"
      class="dropdown-item"
      @click="$emit('select', item)"
    >
      <!-- Station item -->
      <template v-if="item.type === 'station'">
        <span
          class="dot-mini"
          :style="{ background: item.station ? getStationDotColor(item.station.category) : 'var(--signal-red)' }"
        />
        <span class="item-label">{{ item.label }}</span>
        <span class="item-sub">{{ item.sub }}</span>
      </template>

      <!-- Train item -->
      <template v-else-if="item.type === 'train'">
        <TrainTypeTag v-if="item.train" :type="item.train.type" size="sm" />
        <span v-else class="dot-mini" style="background: var(--signal-amber);" />
        <span class="item-label item-label-mono">{{ item.label }}</span>
        <span class="item-sub">{{ item.sub }}</span>
      </template>

      <!-- City item -->
      <template v-else-if="item.type === 'city'">
        <span class="dot-mini" style="background: var(--signal-blue);" />
        <span class="item-label">{{ item.label }}</span>
        <span class="item-sub">{{ item.sub }}</span>
      </template>
    </div>
  </div>

  <div v-else-if="searchStore.query && !searchStore.loading" class="dropdown-empty">
    无匹配结果
  </div>
</template>

<style scoped>
.dropdown {
  max-height: 340px;
  overflow-y: auto;
  padding: var(--space-2);
}

.dropdown-section-title {
  font-family: var(--font-mono);
  font-size: var(--text-2xs);
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: var(--space-2) var(--space-3);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-instant) var(--ease-signal);
}
.dropdown-item:hover {
  background: var(--border-light);
}

.dot-mini {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.item-label {
  font-weight: 500;
  font-size: var(--text-base);
  color: var(--text-primary);
}

.item-label-mono {
  font-family: var(--font-mono);
  font-weight: 600;
}

.item-sub {
  margin-left: auto;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-empty {
  text-align: center;
  padding: var(--space-6);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}
</style>
