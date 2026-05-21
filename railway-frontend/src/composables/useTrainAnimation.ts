import { ref, onUnmounted } from 'vue'
import type { Map } from 'maplibre-gl'
import type { RoutePlan } from '../types/route'

const TRAIN_TYPE_COLORS: Record<string, string> = {
  'G': '#E53E3E',
  'D': '#ED8936',
  'C': '#38A169',
  'Z': '#3182CE',
  'T': '#3182CE',
  'K': '#3182CE',
}

const DASH_ARRAY = [8, 6]

export function useTrainAnimation(mapRef: { value: Map | null }) {
  const activeRoutes = ref<RoutePlan[]>([])
  let animationFrameId: number | null = null
  const dashOffsets: number[] = []
  const speeds: number[] = []

  function getTrainColor(trainNo: string | null): string {
    if (!trainNo) return '#A0AEC0'
    const prefix = trainNo.charAt(0).toUpperCase()
    return TRAIN_TYPE_COLORS[prefix] || '#A0AEC0'
  }

  function getSpeed(trainNo: string | null): number {
    if (!trainNo) return 0.3
    const prefix = trainNo.charAt(0).toUpperCase()
    if (prefix === 'G') return 1.2
    if (prefix === 'D' || prefix === 'C') return 0.8
    return 0.4
  }

  function startAnimation(routes: RoutePlan[]) {
    stopAnimation()
    activeRoutes.value = routes
    dashOffsets.length = 0
    speeds.length = 0
    routes.forEach(r => {
      const firstTrain = r.segments.find(s => s.trainNo)
      dashOffsets.push(0)
      speeds.push(getSpeed(firstTrain?.trainNo ?? null))
    })
    animate()
  }

  function animate() {
    const map = mapRef.value
    if (!map || activeRoutes.value.length === 0) return

    for (let i = 0; i < activeRoutes.value.length; i++) {
      dashOffsets[i] = (dashOffsets[i] + speeds[i]) % (DASH_ARRAY[0] + DASH_ARRAY[1])
    }

    activeRoutes.value.forEach((route, i) => {
      const sourceId = `route-${route.id}`
      if (map.getLayer(`${sourceId}-line`)) {
        const [a, b] = DASH_ARRAY
        const offset = dashOffsets[i]
        map.setPaintProperty(`${sourceId}-line`, 'line-dasharray', [a, b, a, b + offset, a, b])
      }
    })

    animationFrameId = requestAnimationFrame(animate)
  }

  function stopAnimation() {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    activeRoutes.value = []
    dashOffsets.length = 0
  }

  function getPulsePhase(): number {
    return (Date.now() % 1500) / 1500
  }

  onUnmounted(() => stopAnimation())

  return {
    activeRoutes,
    startAnimation,
    stopAnimation,
    getTrainColor,
    getSpeed,
    getPulsePhase,
    TRAIN_TYPE_COLORS,
  }
}
