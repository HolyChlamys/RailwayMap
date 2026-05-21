import { ref, watch, computed } from 'vue'
import { useRoutePlanStore } from '../stores/routePlanStore'
import type { RoutePlan, LineStringCoords } from '../types/route'

/**
 * Composable that generates SVG path data and dash styles
 * for multi-route visualization on the map overlay.
 */
export function useRouteAnimation() {
  const routePlanStore = useRoutePlanStore()
  const svgContent = ref('')

  // ---- Convert coordinate array to SVG path d attribute ----
  function coordsToPath(coords: LineStringCoords): string {
    if (!coords || coords.length === 0) return ''
    const parts = coords.map((pt, i) => {
      const cmd = i === 0 ? 'M' : 'L'
      return `${cmd} ${pt[0]} ${pt[1]}`
    })
    return parts.join(' ')
  }

  // ---- Generate SVG markup for all active plans ----
  function generateSvg(plans: RoutePlan[], activeIndices: number[]): string {
    let html = ''

    plans.forEach((plan, planIdx) => {
      const isActive = activeIndices.includes(planIdx)
      const opacity = isActive ? 1 : 0.15
      const color = plan.color

      plan.segments.forEach((seg, segIdx) => {
        if (!seg.trainNo || !seg.coordinates) return
        const d = coordsToPath(seg.coordinates)
        if (!d) return

        const isSolid = segIdx % 2 === 0
        const dashArray = isSolid ? '24 12' : '8 6'
        const animClass = isSolid ? 'anim-flow' : 'anim-flow-reverse'

        html += `<path class="route-seg ${animClass}" d="${d}" stroke="${color}" opacity="${opacity}" stroke-dasharray="${dashArray}" />`
      })
    })

    // Transfer node markers
    const transferStations = new Set<string>()
    plans.forEach(plan => {
      plan.segments.forEach(seg => {
        if (!seg.trainNo && seg.from) {
          transferStations.add(seg.from)
        }
      })
    })

    return html
  }

  // ---- Reactively update SVG when plans change ----
  watch(
    () => [routePlanStore.plans, routePlanStore.activePlanIndices] as const,
    ([plans, indices]) => {
      svgContent.value = generateSvg(plans as RoutePlan[], indices as number[])
    },
    { deep: true },
  )

  function clearAnimation() {
    svgContent.value = ''
    routePlanStore.clear()
  }

  return {
    svgContent,
    generateSvg,
    clearAnimation,
  }
}
