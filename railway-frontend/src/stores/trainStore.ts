import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Train } from '../types/train'

export const useTrainStore = defineStore('train', () => {
  // ---- State ----
  const currentTrainNo = ref<string | null>(null)
  const trainCache = ref<Map<string, Train>>(new Map())
  const loading = ref(false)

  // ---- Computed ----
  const currentTrain = computed<Train | null>(() => {
    if (!currentTrainNo.value) return null
    return trainCache.value.get(currentTrainNo.value) ?? null
  })

  const hasTrain = computed(() => currentTrain.value !== null)

  // ---- Actions ----
  function setCurrentTrain(no: string | null) {
    currentTrainNo.value = no
  }

  function cacheTrain(train: Train) {
    const existing = trainCache.value.get(train.no)
    // Never overwrite stops with empty data — search results lack stops,
    // and a debounced search can fire after detail fetch, wiping them out.
    if (existing?.stops && !train.stops) {
      trainCache.value.set(train.no, { ...train, stops: existing.stops })
    } else {
      trainCache.value.set(train.no, train)
    }
  }

  function getTrain(no: string): Train | undefined {
    return trainCache.value.get(no)
  }

  function setLoading(l: boolean) {
    loading.value = l
  }

  function clear() {
    currentTrainNo.value = null
  }

  return {
    currentTrainNo,
    trainCache,
    loading,
    currentTrain,
    hasTrain,
    setCurrentTrain,
    cacheTrain,
    getTrain,
    setLoading,
    clear,
  }
})
