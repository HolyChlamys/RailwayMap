<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NSelect, NButton, NSpace, NDatePicker } from 'naive-ui'
import { searchTransfer } from '../../services/transferService'
import type { TransferRequest, TransferResult } from '../../types/transfer'

const emit = defineEmits<{ results: [TransferResult[]] }>()

const from = ref('')
const to = ref('')
const date = ref(Date.now())
const maxTransfers = ref(2)
const preference = ref<'least_time' | 'least_transfer' | 'night_train' | 'least_price'>('least_time')
const searching = ref(false)

const prefOptions = [
  { label: '最少时间', value: 'least_time' },
  { label: '最少换乘', value: 'least_transfer' },
  { label: '最低票价', value: 'least_price' }
]

async function onSubmit() {
  if (!from.value || !to.value) return
  searching.value = true
  try {
    const req: TransferRequest = {
      from: from.value,
      to: to.value,
      date: new Date(date.value).toISOString().split('T')[0],
      maxTransfers: maxTransfers.value,
      preference: preference.value,
      maxResults: 10
    }
    const res = await searchTransfer(req)
    emit('results', res.data.results)
  } finally {
    searching.value = false
  }
}
</script>

<template>
  <n-space vertical>
    <n-input v-model:value="from" placeholder="出发站" />
    <n-input v-model:value="to" placeholder="到达站" />
    <n-date-picker v-model:value="date" type="date" />
    <n-select v-model:value="maxTransfers" :options="[
      { label: '直达', value: 0 }, { label: '1次换乘', value: 1 },
      { label: '2次换乘', value: 2 }, { label: '3次换乘', value: 3 }
    ]" />
    <n-select v-model:value="preference" :options="prefOptions" />
    <n-button type="primary" :loading="searching" block @click="onSubmit">
      搜索
    </n-button>
  </n-space>
</template>
