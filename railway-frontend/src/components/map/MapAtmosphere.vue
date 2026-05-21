<script setup lang="ts">
// Subtle paper texture + compass rose overlay
// Renders as a non-interactive atmosphere layer on top of the map
</script>

<template>
  <div class="map-atmosphere">
    <!-- Paper grain texture -->
    <div class="grain-overlay" />

    <!-- Compass rose (bottom-left corner) -->
    <div class="compass-rose">
      <svg viewBox="0 0 40 40" width="36" height="36">
        <!-- Outer ring -->
        <circle cx="20" cy="20" r="18" fill="none" stroke="var(--text-secondary)" stroke-width="1" opacity="0.4" />
        <!-- North pointer -->
        <polygon points="20,4 24,16 20,14 16,16" fill="var(--signal-red)" opacity="0.9" />
        <!-- South pointer -->
        <polygon points="20,36 24,24 20,26 16,24" fill="var(--text-tertiary)" opacity="0.5" />
        <!-- N label -->
        <text x="20" y="9" text-anchor="middle" font-size="7" font-family="var(--font-display)" font-weight="700" fill="var(--text-primary)">N</text>
      </svg>
    </div>

    <!-- Scale bar placeholder (bottom-left, next to compass) -->
    <div class="scale-bar">
      <span class="scale-label">~100 km</span>
    </div>
  </div>
</template>

<style scoped>
.map-atmosphere {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 5;
}

/* Paper grain — noise texture via CSS */
.grain-overlay {
  position: absolute;
  inset: 0;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.5'/%3E%3C/svg%3E");
  background-size: 256px 256px;
}

/* Compass rose */
.compass-rose {
  position: absolute;
  bottom: var(--space-4);
  left: var(--space-4);
}

/* Scale bar */
.scale-bar {
  position: absolute;
  bottom: var(--space-5);
  left: calc(var(--space-4) + 44px);
}

.scale-label {
  font-family: var(--font-mono);
  font-size: var(--text-2xs);
  color: var(--text-tertiary);
  letter-spacing: 1px;
}
</style>
