import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, AgentMessageContent, AgentPanelState, QuickSuggestion, AgentInstruction, FlyToStationInstruction, HighlightTrainInstruction, HighlightRoutesInstruction, HighlightIsochroneInstruction } from '../types/agent'
import { useMapStore } from './mapStore'
import { useStationStore } from './stationStore'
import { useTrainStore } from './trainStore'
import { useRoutePlanStore } from './routePlanStore'

export const useAgentStore = defineStore('agent', () => {
  // ---- State ----
  const messages = ref<ChatMessage[]>([])
  const panelState = ref<AgentPanelState>('closed')
  const isProcessing = ref(false)

  // ---- Computed ----
  const isOpen = computed(() => panelState.value === 'open')
  const messageCount = computed(() => messages.value.length)

  const defaultQuickSuggestions: QuickSuggestion[] = [
    { label: '北京到广州怎么走', prompt: '北京到广州怎么走' },
    { label: '查询G1车次', prompt: '查询G1车次' },
    { label: '上海虹桥有哪些车', prompt: '上海虹桥有哪些车' },
  ]

  const quickSuggestions = ref<QuickSuggestion[]>([...defaultQuickSuggestions])

  // ---- Actions ----
  function openPanel() {
    panelState.value = 'open'
    if (messages.value.length === 0) {
      addWelcomeMessage()
    }
  }

  function closePanel() {
    panelState.value = 'closed'
  }

  function togglePanel() {
    if (panelState.value === 'open') closePanel()
    else openPanel()
  }

  function addMessage(role: 'user' | 'agent', content: AgentMessageContent) {
    messages.value.push({
      id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      role,
      content,
      timestamp: new Date(),
    })
  }

  function addWelcomeMessage() {
    messages.value.push({
      id: 'welcome',
      role: 'agent',
      content: {
        text: '你好！我是铁路助手，可以帮你：\n\n🔍 **查询信息** — 车站详情、车次信息、城市车站\n🗺️ **路径规划** — 输入起点、终点和偏好，我帮你规划中转路线\n\n直接告诉我你的需求。',
      },
      timestamp: new Date(),
    })
  }

  function setProcessing(p: boolean) {
    isProcessing.value = p
  }

  function dispatchInstruction(instruction: AgentInstruction) {
    const mapStore = useMapStore()
    const stationStore = useStationStore()
    const trainStore = useTrainStore()
    const routePlanStore = useRoutePlanStore()

    switch (instruction.action) {
      case 'flyToStation': {
        const { stationId } = instruction as FlyToStationInstruction
        mapStore.setFocusStation(stationId)
        stationStore.setCurrentStation(stationId)
        break
      }
      case 'highlightTrain': {
        const { trainNo } = instruction as HighlightTrainInstruction
        mapStore.setFocusTrain(trainNo)
        trainStore.setCurrentTrain(trainNo)
        break
      }
      case 'highlightRoutes': {
        const { routeIds } = instruction as HighlightRoutesInstruction
        routePlanStore.setActivePlanIds(routeIds)
        break
      }
      case 'highlightIsochrone': {
        const { stationId } = instruction as HighlightIsochroneInstruction
        mapStore.setFocusStation(stationId)
        break
      }
      case 'openPanel': {
        // Panel opening handled by App.vue watch on stores
        break
      }
      case 'openModal': {
        // Modal opening handled by component
        break
      }
      case 'clearHighlights': {
        mapStore.clearAllFocus()
        routePlanStore.clear()
        break
      }
    }
  }

  function setQuickSuggestions(sugs: QuickSuggestion[]) {
    quickSuggestions.value = sugs
  }

  function clearMessages() {
    messages.value = []
    addWelcomeMessage()
  }

  return {
    messages,
    panelState,
    isProcessing,
    isOpen,
    messageCount,
    defaultQuickSuggestions,
    quickSuggestions,
    openPanel,
    closePanel,
    togglePanel,
    addMessage,
    setProcessing,
    clearMessages,
    dispatchInstruction,
    setQuickSuggestions,
  }
})
