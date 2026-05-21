import { useAgentStore } from '../stores/agentStore'
import { agentApi } from '../api/agentApi'

let sessionId: string | null = null

export function useAgentChat() {
  const agentStore = useAgentStore()

  async function sendMessage(text: string) {
    agentStore.addMessage('user', { text })
    agentStore.setProcessing(true)

    try {
      const response = await agentApi.chat({
        session_id: sessionId,
        message: text,
      })

      sessionId = response.session_id

      agentStore.addMessage('agent', {
        text: response.text,
        instructions: response.instructions,
        suggestions: response.suggestions,
      })

      // Dispatch instructions to drive map interactions
      for (const instruction of response.instructions) {
        agentStore.dispatchInstruction(instruction)
      }

      // Update quick suggestions for follow-up
      if (response.suggestions.length > 0) {
        agentStore.setQuickSuggestions(
          response.suggestions.map(s => ({ label: s, prompt: s }))
        )
      }
    } catch (err) {
      agentStore.addMessage('agent', {
        text: `抱歉，请求失败：${err instanceof Error ? err.message : '未知错误'}。请稍后重试。`,
      })
    } finally {
      agentStore.setProcessing(false)
    }
  }

  return { sendMessage }
}
