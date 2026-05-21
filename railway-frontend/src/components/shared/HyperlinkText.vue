<script setup lang="ts">
const props = withDefaults(defineProps<{
  /** Link type: 'station' | 'train' | 'city' */
  type: 'station' | 'train' | 'city'
  /** Payload: station ID, train number, or city name */
  action: string
  /** Display text */
  label?: string
}>(), {
  label: undefined,
})

const emit = defineEmits<{
  navigate: [type: string, action: string]
}>()

function handleClick() {
  emit('navigate', props.type, props.action)
}
</script>

<template>
  <a
    class="hyperlink"
    href="#"
    @click.prevent="handleClick"
  >
    {{ props.label ?? props.action }}
  </a>
</template>

<style scoped>
.hyperlink {
  font-family: inherit;
  color: var(--signal-blue);
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
  transition: opacity var(--duration-instant) var(--ease-signal);
}
.hyperlink:hover {
  opacity: 0.8;
}
</style>
