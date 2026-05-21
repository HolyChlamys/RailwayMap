<script setup lang="ts">
import { useRouteAnimation } from '../../composables/useRouteAnimation'

const { svgContent } = useRouteAnimation()
</script>

<template>
  <svg
    v-if="svgContent"
    class="route-anim-layer"
    viewBox="0 0 1920 1080"
    preserveAspectRatio="none"
    v-html="svgContent"
  />
</template>

<style scoped>
.route-anim-layer {
  position: absolute;
  inset: 0;
  z-index: 4;
  pointer-events: none;
}

:deep(.route-seg) {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 4px currentColor);
  transition: opacity 0.4s var(--ease-signal);
}

:deep(.anim-flow) {
  animation: flow 1.2s linear infinite;
}

:deep(.anim-flow-reverse) {
  animation: flow-reverse 1.8s linear infinite;
}

/* Crossfade transition when route plan changes */
.route-anim-layer {
  transition: opacity 0.35s var(--ease-signal);
}

@keyframes flow {
  to { stroke-dashoffset: -36; }
}

@keyframes flow-reverse {
  to { stroke-dashoffset: 28; }
}
</style>
