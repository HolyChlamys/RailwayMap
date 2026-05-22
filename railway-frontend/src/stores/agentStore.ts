import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, AgentMessageContent, AgentPanelState, QuickSuggestion } from '../types/agent'

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
  function loadHistory() {
    try {
      const saved = localStorage.getItem('railwaymap_agent_history')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          messages.value = parsed.map(m => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }))
          return
        }
      }
    } catch (e) {
      console.warn('Failed to load agent history', e)
    }
    if (messages.value.length === 0) {
      addWelcomeMessage()
    }
  }

  function saveHistory() {
    try {
      localStorage.setItem('railwaymap_agent_history', JSON.stringify(messages.value))
    } catch (e) {
      console.warn('Failed to save agent history', e)
    }
  }

  function openPanel() {
    panelState.value = 'open'
    if (messages.value.length === 0) {
      loadHistory()
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
    saveHistory()
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
    saveHistory()
  }

  function setProcessing(p: boolean) {
    isProcessing.value = p
  }

  function setQuickSuggestions(sugs: QuickSuggestion[]) {
    quickSuggestions.value = sugs
  }

  function clearMessages() {
    messages.value = []
    localStorage.removeItem('railwaymap_agent_history')
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
    setQuickSuggestions,
  }
})
