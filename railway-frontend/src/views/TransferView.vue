<script setup lang="ts">
import TransferSearchForm from '../components/transfer/TransferSearchForm.vue'
import TransferResultList from '../components/transfer/TransferResultList.vue'
import TransferTimeline from '../components/transfer/TransferTimeline.vue'
import { ref } from 'vue'
import type { TransferResult } from '../types/transfer'

const results = ref<TransferResult[]>([])
const selectedResult = ref<TransferResult | null>(null)

function onResultsReceived(data: TransferResult[]) {
  results.value = data
}

function onSelectResult(result: TransferResult) {
  selectedResult.value = result
}
</script>

<template>
  <div class="flex h-full">
    <div class="w-96 flex-shrink-0 border-r overflow-y-auto p-4">
      <TransferSearchForm @results="onResultsReceived" />
      <TransferResultList
        :results="results"
        @select="onSelectResult"
        class="mt-4"
      />
    </div>
    <div class="flex-1 p-4 overflow-y-auto">
      <TransferTimeline v-if="selectedResult" :result="selectedResult" />
      <div v-else class="text-gray-400 text-center mt-20">
        请选择换乘方案查看详情
      </div>
    </div>
  </div>
</template>
