<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useStationStore } from '../../stores/stationStore'
import { STATION_TYPE_LABELS } from '../../types/station'
import type { TimetableEntry } from '../../types/station'
import type { TrainType } from '../../types/train'
import TrainTypeTag from '../shared/TrainTypeTag.vue'
import HyperlinkText from '../shared/HyperlinkText.vue'

const PAGE_SIZE = 40

const stationStore = useStationStore()

const emit = defineEmits<{
  close: []
  navigate: [type: string, action: string]
}>()

const visible = defineModel<boolean>('visible', { default: false })
const displayCount = ref(PAGE_SIZE)

const station = computed(() => stationStore.currentStation)
const timetable = computed<TimetableEntry[]>(() => station.value?.timetable ?? [])

function asTrainType(t: string): TrainType {
  return t as TrainType
}

const displayed = computed(() => timetable.value.slice(0, displayCount.value))
const hasMore = computed(() => displayCount.value < timetable.value.length)

// Reset page when modal opens with new data
watch(visible, (v) => {
  if (v) displayCount.value = PAGE_SIZE
})

function loadMore() {
  displayCount.value = Math.min(displayCount.value + PAGE_SIZE, timetable.value.length)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible && station" class="modal-backdrop" @click.self="emit('close')">
        <div class="modal-container">
          <!-- Header -->
          <div class="modal-header">
            <div>
              <h3 class="modal-title">{{ station.name }} — 经停车次</h3>
              <p class="modal-subtitle">
                {{ station.city }} · {{ STATION_TYPE_LABELS[station.category] }} · 共 {{ timetable.length }} 趟列车
              </p>
            </div>
            <button class="modal-close" @click="emit('close')" title="关闭">
              ✕
            </button>
          </div>

          <!-- Table -->
          <div class="modal-body">
            <table v-if="timetable.length > 0" class="timetable-table">
              <thead>
                <tr>
                  <th>类型</th>
                  <th>车次</th>
                  <th>始发站</th>
                  <th>终到站</th>
                  <th>到达</th>
                  <th>发车</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in displayed" :key="t.trainNo">
                  <td><TrainTypeTag :type="asTrainType(t.trainType)" size="sm" /></td>
                  <td>
                    <HyperlinkText
                      type="train"
                      :action="t.trainNo"
                      @navigate="(type, a) => { emit('close'); emit('navigate', type, a) }"
                    />
                  </td>
                  <td>
                    <HyperlinkText
                      type="station"
                      :action="t.departStation"
                      @navigate="(type, a) => { emit('close'); emit('navigate', type, a) }"
                    />
                  </td>
                  <td>
                    <HyperlinkText
                      type="station"
                      :action="t.arriveStation"
                      @navigate="(type, a) => { emit('close'); emit('navigate', type, a) }"
                    />
                  </td>
                  <td class="time-cell">{{ t.arriveTime || '—' }}</td>
                  <td class="time-cell">{{ t.departTime || '—' }}</td>
                </tr>
              </tbody>
            </table>

            <div v-if="timetable.length === 0" class="empty-state">
              暂无经停车次数据
            </div>

            <button
              v-if="hasMore"
              class="btn-load-more"
              @click="loadMore"
            >
              显示更多 ({{ timetable.length - displayCount }} 趟)
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 600;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-container {
  background: var(--glass-bg-active);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  width: 680px;
  max-width: calc(100vw - 48px);
  max-height: 75vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--space-6);
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-light);
}

.modal-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.modal-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-top: 4px;
}

.modal-close {
  width: 34px;
  height: 34px;
  border: none;
  background: var(--border-light);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: all var(--duration-fast);
}
.modal-close:hover {
  background: var(--border-medium);
  color: var(--text-primary);
}

/* Body */
.modal-body {
  overflow-y: auto;
  flex: 1;
  padding: var(--space-6);
}

/* Table */
.timetable-table {
  width: 100%;
  border-collapse: collapse;
}

.timetable-table th {
  text-align: left;
  font-family: var(--font-mono);
  font-size: var(--text-2xs);
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 1px;
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--border-medium);
}

.timetable-table td {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-base);
  border-bottom: 1px solid var(--border-light);
}

.timetable-table tbody tr {
  transition: background var(--duration-instant);
}
.timetable-table tbody tr:hover {
  background: var(--border-light);
}

.time-cell {
  font-family: var(--font-mono);
  font-weight: 500;
}

.btn-load-more {
  width: 100%;
  padding: 8px var(--space-4);
  margin-top: var(--space-4);
  border: 1px dashed var(--border-medium);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.btn-load-more:hover {
  border-color: var(--signal-blue);
  color: var(--signal-blue);
}

.empty-state {
  text-align: center;
  padding: var(--space-10);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

/* Transitions */
.modal-fade-enter-active {
  transition: opacity var(--duration-normal) var(--ease-signal);
}
.modal-fade-leave-active {
  transition: opacity 180ms var(--ease-signal);
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-container {
  transition: transform var(--duration-normal) var(--ease-signal);
}
.modal-fade-leave-active .modal-container {
  transition: transform 180ms var(--ease-signal);
}
.modal-fade-enter-from .modal-container {
  transform: scale(0.94) translateY(12px);
}
.modal-fade-leave-to .modal-container {
  transform: scale(0.96) translateY(8px);
}
</style>
