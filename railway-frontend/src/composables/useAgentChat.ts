import { useAgentStore } from '../stores/agentStore'
import { useStationStore } from '../stores/stationStore'
import { useTrainStore } from '../stores/trainStore'
import { useRoutePlanStore } from '../stores/routePlanStore'
import { useAgentDispatch } from './useAgentDispatch'
import { agentApi } from '../api/agentApi'
import { mapToStation } from '../types/station'
import { mapToTrainDetail } from '../types/train'
import type { Station } from '../types/station'
import type { Train } from '../types/train'

let sessionId: string | undefined = undefined

export function useAgentChat() {
  const agentStore = useAgentStore()
  const stationStore = useStationStore()
  const trainStore = useTrainStore()
  const routePlanStore = useRoutePlanStore()
  const { instruction: agentInstruction } = useAgentDispatch()

  function cacheStationFromResponse(station: Record<string, unknown> | null | undefined) {
    if (!station) return
    const s: Station = mapToStation(station)
    stationStore.cacheStation(s)
  }

  function cacheTrainFromResponse(train: Record<string, unknown> | null | undefined) {
    if (!train) return
    const t: Train = mapToTrainDetail(train)
    trainStore.cacheTrain(t)
  }

  function cacheRoutesFromResponse(routes: Record<string, unknown>[] | null | undefined) {
    if (!routes || routes.length === 0) return null
    // Build simple route plans from agent response for map rendering
    const plans = routes.map((r, i) => ({
      id: (r.id as string) || `plan-${i}`,
      label: `方案${i + 1}`,
      segments: ((r.segments as Record<string, unknown>[]) || []).map((seg: Record<string, unknown>) => ({
        trainNo: (seg.trainNo as string) || null,
        from: (seg.fromStation as string) || (seg.from as string) || '',
        to: (seg.toStation as string) || (seg.to as string) || '',
        depart: (seg.departTime as string) || (seg.depart as string) || '',
        arrive: (seg.arriveTime as string) || (seg.arrive as string) || '',
        coordinates: (seg.coordinates as [number, number][]) || null,
      })),
      totalDurationMin: (r.totalTimeMin as number) || (r.totalDurationMin as number) || 0,
      transfers: (r.transferCount as number) || (r.transfers as number) || 0,
      color: `var(--route-${(i % 6) + 1})`,
    }))
    routePlanStore.setPlans(plans)
    return plans
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
      cacheTrainFromResponse(response.train)
      const plans = cacheRoutesFromResponse(response.routes)

      agentStore.addMessage('agent', {
        text: response.text,
        instructions: response.instructions,
        suggestions: response.suggestions,
        routePlans: plans || undefined
      })

      // Dispatch instructions to drive map interactions (station cache now populated)
      for (const inst of response.instructions) {
        agentInstruction.value = inst
      }

      // Update quick suggestions for follow-up
      if (response.suggestions.length > 0) {
        agentStore.setQuickSuggestions(
          response.suggestions.map(s => ({ label: s, prompt: s }))
        )
      }
    } catch (err) {
      console.error('Agent chat error:', err)
      agentStore.addMessage('agent', {
        text: `抱歉，请求失败：${err instanceof Error ? err.message : '未知错误'}。请稍后重试。`,
      })
    } finally {
      agentStore.setProcessing(false)
    }
  }

  return { sendMessage }
}
