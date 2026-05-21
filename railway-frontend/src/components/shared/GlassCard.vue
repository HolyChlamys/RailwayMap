<script setup lang="ts">
withDefaults(defineProps<{
  /** Optional title shown in the card header */
  title?: string
  /** Remove padding when content needs full bleed */
  noPadding?: boolean
}>(), {
  title: undefined,
  noPadding: false,
})
</script>

<template>
  <div class="glass-card">
    <div v-if="title || $slots.header" class="glass-card-header">
      <slot name="header">
        <span class="glass-card-title">{{ title }}</span>
      </slot>
    </div>
    <div class="glass-card-body" :class="{ 'no-padding': noPadding }">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.glass-card-header {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-light);
}

.glass-card-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
}

.glass-card-body {
  padding: var(--space-4);
}

.glass-card-body.no-padding {
  padding: 0;
}
</style>
