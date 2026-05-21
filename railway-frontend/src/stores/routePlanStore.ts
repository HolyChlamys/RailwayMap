import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RoutePlan, RouteConstraint, RouteSegment, LineStringCoords } from '../types/route'
import { ROUTE_PALETTE } from '../types/route'

export const useRoutePlanStore = defineStore('routePlan', () => {
  // ---- State ----
  const plans = ref<RoutePlan[]>([])
  const activePlanIndices = ref<number[]>([])
  const loading = ref(false)

  // ---- Computed ----
  const hasPlans = computed(() => plans.value.length > 0)
  const activePlans = computed(() =>
    activePlanIndices.value.map(i => plans.value[i]).filter(Boolean)
  )

  // ---- Actions ----
  function setPlans(newPlans: RoutePlan[]) {
    plans.value = newPlans
    activePlanIndices.value = newPlans.map((_, i) => i)
  }

  function filterByConstraint(constraint: Partial<RouteConstraint>): number[] {
    let indices = plans.value.map((_, i) => i)

    if (constraint.preferTrainTypes?.length) {
      indices = indices.filter(i => {
        return plans.value[i].segments.some(s => s.trainNo && constraint.preferTrainTypes!.some(t => s.trainNo!.startsWith(t)))
      })
    }

    if (constraint.maxTransfers !== undefined) {
      indices = indices.filter(i => plans.value[i].transfers <= constraint.maxTransfers!)
    }

    activePlanIndices.value = indices
    return indices
  }

  function resetFilter() {
    activePlanIndices.value = plans.value.map((_, i) => i)
  }

  function clear() {
    plans.value = []
    activePlanIndices.value = []
  }

  function setLoading(l: boolean) {
    loading.value = l
  }

  return {
    plans,
    activePlanIndices,
    loading,
    hasPlans,
    activePlans,
    setPlans,
    filterByConstraint,
    resetFilter,
    clear,
    setLoading,
  }
})

// ---- Mock route plan paths (SVG coordinate-space for prototype) ----
export const MOCK_ROUTE_COORDS: Record<string, LineStringCoords> = {
  'G1': [[1240, 314], [1280, 370], [1340, 440], [1500, 560]],
  'G2': [[1240, 314], [1190, 390], [1155, 470], [1160, 540], [1110, 700], [1100, 780]],
  'G3': [[1240, 314], [1280, 390], [1320, 440], [1400, 518]],
  'G8': [[1500, 560], [1440, 510], [1380, 454], [1340, 460], [1280, 380], [1240, 314]],
  'G89': [[950, 420], [880, 440], [830, 470], [780, 500], [770, 540], [750, 630]],
  'D301': [[1248, 300], [1190, 320], [1140, 360], [1160, 390], [1120, 420], [1060, 500], [1000, 530], [950, 420]],
  'D940': [[750, 630], [780, 640], [850, 670], [940, 710], [1020, 740], [1080, 780], [1100, 780]],
  'D101': [[1248, 300], [1350, 250], [1450, 200], [1560, 150], [1580, 120]],
  'Z55': [[550, 380], [600, 390], [650, 400], [700, 410], [750, 420], [850, 440], [950, 420], [1000, 430], [1100, 440], [1150, 440], [1220, 380], [1230, 330]],
}

export function buildMockPlan(from: string, to: string): RoutePlan[] {
  // Build 3 mock plans between Beijing and Guangzhou
  return [
    {
      id: 'plan-1',
      label: '方案一',
      segments: [
        { trainNo: 'G1', from: '北京南', to: '济南西', depart: '09:00', arrive: '10:22', coordinates: MOCK_ROUTE_COORDS['G1'] },
        { trainNo: null, from: '济南西', to: '济南西', depart: '10:22', arrive: '10:25', coordinates: null },
        { trainNo: 'G2', from: '济南西', to: '广州南', depart: '10:25', arrive: '16:45', coordinates: MOCK_ROUTE_COORDS['G2'] },
      ],
      totalDurationMin: 465,
      transfers: 1,
      color: ROUTE_PALETTE[0],
    },
    {
      id: 'plan-2',
      label: '方案二',
      segments: [
        { trainNo: 'G3', from: '北京南', to: '南京南', depart: '14:00', arrive: '17:30', coordinates: MOCK_ROUTE_COORDS['G3'] },
        { trainNo: null, from: '南京南', to: '南京南', depart: '17:30', arrive: '17:35', coordinates: null },
        { trainNo: 'G1', from: '南京南', to: '上海虹桥', depart: '17:35', arrive: '18:45', coordinates: MOCK_ROUTE_COORDS['G8'] },
        { trainNo: null, from: '上海虹桥', to: '上海虹桥', depart: '18:45', arrive: '19:00', coordinates: null },
        { trainNo: 'G2', from: '上海虹桥', to: '广州南', depart: '19:00', arrive: '23:45', coordinates: MOCK_ROUTE_COORDS['G2'] },
      ],
      totalDurationMin: 585,
      transfers: 2,
      color: ROUTE_PALETTE[1],
    },
    {
      id: 'plan-3',
      label: '方案三',
      segments: [
        { trainNo: 'D301', from: '北京', to: '西安北', depart: '11:15', arrive: '17:40', coordinates: MOCK_ROUTE_COORDS['D301'] },
        { trainNo: null, from: '西安北', to: '西安北', depart: '17:40', arrive: '18:00', coordinates: null },
        { trainNo: 'G89', from: '西安北', to: '成都东', depart: '18:00', arrive: '21:35', coordinates: MOCK_ROUTE_COORDS['G89'] },
        { trainNo: null, from: '成都东', to: '成都东', depart: '21:35', arrive: '22:00', coordinates: null },
        { trainNo: 'D940', from: '成都东', to: '广州南', depart: '22:00', arrive: '08:30', coordinates: MOCK_ROUTE_COORDS['D940'] },
      ],
      totalDurationMin: 1275,
      transfers: 2,
      color: ROUTE_PALETTE[2],
    },
  ]
}
