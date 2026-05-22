import { ref, watch } from 'vue'
import type { AgentInstruction, FlyToStationInstruction, HighlightTrainInstruction, HighlightRoutesInstruction, HighlightIsochroneInstruction } from '../types/agent'
import { useMapStore } from '../stores/mapStore'
import { useStationStore } from '../stores/stationStore'
import { useTrainStore } from '../stores/trainStore'
import { useRoutePlanStore } from '../stores/routePlanStore'

// Module-level ref so all callers (AgentPanel, useAgentChat) share the same instance
const instruction = ref<AgentInstruction | null>(null)
let initialized = false

export function useAgentDispatch() {
  const mapStore = useMapStore()
  const stationStore = useStationStore()
  const trainStore = useTrainStore()
  const routePlanStore = useRoutePlanStore()

  // Set up the watcher once; subsequent calls return the same shared ref
  if (!initialized) {
    initialized = true
    watch(instruction, (inst) => {
      if (!inst) return
      switch (inst.action) {
        case 'flyToStation': {
          const { stationId } = inst as FlyToStationInstruction
          const id = parseInt(stationId, 10)
          mapStore.setFocusStation(stationId)
          stationStore.setCurrentStation(isNaN(id) ? null : id)
          break
        }
        case 'highlightTrain': {
          const { trainNo } = inst as HighlightTrainInstruction
          mapStore.setFocusTrain(trainNo)
          trainStore.setCurrentTrain(trainNo)
          break
        }
        case 'highlightRoutes': {
          const { routeIds } = inst as HighlightRoutesInstruction
          routePlanStore.setActivePlanIds(routeIds)
          break
        }
        case 'highlightIsochrone': {
          const { stationId } = inst as HighlightIsochroneInstruction
          mapStore.setFocusStation(stationId)
          break
        }
        case 'openPanel':
        case 'openModal':
          break
        case 'clearHighlights': {
          mapStore.clearAllFocus()
          routePlanStore.clear()
          break
        }
      }
    })
  }

  return { instruction }
}
