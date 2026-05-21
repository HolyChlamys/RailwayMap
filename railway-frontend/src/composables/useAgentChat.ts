import { useAgentStore } from '../stores/agentStore'
import { useStationStore } from '../stores/stationStore'
import { useRoutePlanStore } from '../stores/routePlanStore'
import { agentApi } from '../api/agentApi'
import { mapToStation } from '../types/station'
import type { Station } from '../types/station'

let sessionId: string | null = null

export function useAgentChat() {
  const agentStore = useAgentStore()
  const stationStore = useStationStore()
  const routePlanStore = useRoutePlanStore()

  function cacheStationFromResponse(station: Record<string, unknown> | null | undefined) {
    if (!station) return
    const s: Station = mapToStation(station)
    stationStore.cacheStation(s)
  }

  function cacheRoutesFromResponse(routes: Record<string, unknown>[] | null | undefined) {
    if (!routes || routes.length === 0) return
    // Build simple route plans from agent response for map rendering
    const plans = routes.map((r, i) => ({
      id: (r.id as string) || `plan-${i}`,
      label: `方案${i + 1}`,
      segments: ((r.segments as Record<string, unknown>[]) || []).map((seg: Record<string, unknown>) => ({
        trainNo: (seg.trainNo as string) || null,
        from: (seg.from as string) || '',
        to: (seg.to as string) || '',
        depart: (seg.depart as string) || '',
        arrive: (seg.arrive as string) || '',
        coordinates: (seg.coordinates as [number, number][]) || null,
      })),
      totalDurationMin: (r.totalDurationMin as number) || 0,
      transfers: (r.transfers as number) || 0,
      color: `var(--route-${(i % 6) + 1})`,
    }))
    routePlanStore.setPlans(plans)
  }

  async function sendMessage(text: string) {
    agentStore.addMessage('user', { text })
    agentStore.setProcessing(true)

    try {
      const response = await agentApi.chat({
        session_id: sessionId,
        message: text,
      })

      sessionId = response.session_id

      // Cache station/route data BEFORE dispatching instructions
      cacheStationFromResponse(response.station)
      cacheRoutesFromResponse(response.routes)

      agentStore.addMessage('agent', {
        text: response.text,
        instructions: response.instructions,
        suggestions: response.suggestions,
      })

      // Dispatch instructions to drive map interactions (station cache now populated)
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
