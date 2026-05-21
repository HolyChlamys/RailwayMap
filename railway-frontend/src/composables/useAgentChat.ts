import { useAgentStore } from '../stores/agentStore'
import { useStationStore } from '../stores/stationStore'
import { useTrainStore } from '../stores/trainStore'
import { useMapStore } from '../stores/mapStore'
import { useRoutePlanStore, buildMockPlan } from '../stores/routePlanStore'
import type { AgentMessageContent } from '../types/agent'
import { STATION_TYPE_LABELS } from '../types/station'

/**
 * Composable for Agent chat logic.
 * Parses user input intents and dispatches to appropriate stores.
 * Currently uses mock data — replace with real API calls in the future.
 */
export function useAgentChat() {
  const agentStore = useAgentStore()
  const stationStore = useStationStore()
  const trainStore = useTrainStore()
  const mapStore = useMapStore()
  const routePlanStore = useRoutePlanStore()

  function sendMessage(text: string) {
    // Add user message
    agentStore.addMessage('user', { text })
    agentStore.setProcessing(true)

    // Simulate network delay
    setTimeout(() => {
      processIntent(text)
      agentStore.setProcessing(false)
    }, 800)
  }

  function processIntent(text: string) {
    const t = text.trim()

    // --- Train query ---
    const trainMatch = t.match(/(?:查询|查看|搜索)?\s*([GDCZTKL]\d+)/i)
    if (trainMatch) {
      const no = trainMatch[1].toUpperCase()
      const train = trainStore.getTrain(no)
      if (train) {
        trainStore.setCurrentTrain(no)
        mapStore.setFocusTrain(no)
        agentStore.addMessage('agent', {
          text: `${no} 次列车，${train.from} → ${train.to}，${train.departTime}—${train.arriveTime}，全程 ${Math.floor(train.durationMin / 60)}h${train.durationMin % 60}min。`,
          trainNo: no,
        })
      } else {
        agentStore.addMessage('agent', { text: `抱歉，未找到车次 ${no} 的信息。` })
      }
      return
    }

    // --- Station query ---
    const stationQueryMatch = t.match(/(?:查询|查看|搜索)?(.+?)(?:站|有哪些车|的信息)/)
    if (stationQueryMatch) {
      const name = stationQueryMatch[1]
      let foundStation = false
      stationStore.stationCache.forEach((s) => {
        if (s.name === name) {
          stationStore.setCurrentStation(s.id)
          mapStore.setFocusStation(String(s.id))
          agentStore.addMessage('agent', {
            text: `${s.name}，${s.city} · ${STATION_TYPE_LABELS[s.category]}，途经 ${s.routes || [].length} 趟列车。\n\n详细信息已在左侧面板展示。`,
            stationId: String(s.id),
          })
          foundStation = true
        }
      })
      if (!foundStation) {
        agentStore.addMessage('agent', { text: `抱歉，未找到车站「${name}」的信息。` })
      }
      return
    }

    // --- Route planning ---
    const routeMatch = t.match(/(?:从|由)?(.+?)(?:到|去|→|至)(.+?)(?:怎么走|怎么去|路线|中转|$)/)
    if (routeMatch) {
      const from = routeMatch[1].trim()
      const to = routeMatch[2].trim()
      let fromExists = false
      let toExists = false
      stationStore.stationCache.forEach(s => {
        if (s.name === from) fromExists = true
        if (s.name === to) toExists = true
      })

      if (fromExists && toExists) {
        const plans = buildMockPlan(from, to)
        routePlanStore.setPlans(plans)

        const planTexts = plans.map((p, i) => {
          const segText = p.segments
            .filter(s => s.trainNo)
            .map(s => `${s.from} —${s.trainNo}→ ${s.to}`)
            .join(' → ')
          return `**${p.label}**：${segText}\n⏱ ${Math.floor(p.totalDurationMin / 60)}h${p.totalDurationMin % 60}min · 🔄 ${p.transfers} 次换乘`
        }).join('\n\n')

        agentStore.addMessage('agent', {
          text: `从 **${from}** 到 **${to}**，找到 ${plans.length} 条路线：\n\n${planTexts}\n\n不同路线以不同颜色在地图上高亮，虚线/实线区分不同车次段落。你可以进一步筛选（如"最短时间"、"高铁优先"）。`,
          routePlans: plans,
        })
      } else {
        agentStore.addMessage('agent', { text: `抱歉，未找到从 ${from} 到 ${to} 的中转路线。请确认站名是否正确。` })
      }
      return
    }

    // --- Constraint filtering ---
    if (t.includes('最短时间') || t.includes('最快')) {
      if (routePlanStore.hasPlans) {
        routePlanStore.filterByConstraint({ preferTrainTypes: ['G'] })
        agentStore.addMessage('agent', { text: '已按最短时间/高铁优先筛选，地图上仅保留符合条件的高铁线路。' })
      } else {
        agentStore.addMessage('agent', { text: '请先进行路径规划查询（如输入"北京到广州怎么走"）。' })
      }
      return
    }

    if (t.includes('高铁') || t.includes('G字头')) {
      if (routePlanStore.hasPlans) {
        routePlanStore.filterByConstraint({ preferTrainTypes: ['G'] })
        agentStore.addMessage('agent', { text: '已筛选高铁线路，地图已更新。' })
      } else {
        agentStore.addMessage('agent', { text: '请先进行路径规划查询。' })
      }
      return
    }

    if (t.includes('最少换乘')) {
      if (routePlanStore.hasPlans) {
        routePlanStore.filterByConstraint({ maxTransfers: 1 })
        agentStore.addMessage('agent', { text: '已筛选换乘次数最少的路线，地图已更新。' })
      } else {
        agentStore.addMessage('agent', { text: '请先进行路径规划查询。' })
      }
      return
    }

    // --- Fallback ---
    agentStore.addMessage('agent', {
      text: `好的，关于「${t}」，目前我可以帮你：\n\n• **查询车次** — 输入"G1"或"查询G1车次"\n• **查询车站** — 输入"北京站"或"上海虹桥有哪些车"\n• **路径规划** — 输入"北京到广州怎么走"\n• **筛选路线** — 输入"最短时间"、"高铁优先"、"最少换乘"`,
    })
  }

  return { sendMessage }
}
