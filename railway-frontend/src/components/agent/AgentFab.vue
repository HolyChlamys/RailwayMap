<script setup lang="ts">
import { useAgentStore } from '../../stores/agentStore'

const agentStore = useAgentStore()
</script>

<template>
  <button
    class="agent-fab"
    :class="{ hidden: agentStore.isOpen }"
    title="铁路助手"
    @click="agentStore.openPanel()"
  >
    <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="3" y="3" width="18" height="14" rx="2" />
      <path d="M7 21l2-4h6l2 4" />
    </svg>
  </button>
</template>

<style scoped>
.agent-fab {
  position: absolute;
  bottom: var(--space-6);
  right: var(--space-6);
  z-index: 400;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, var(--signal-red), var(--signal-amber));
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(214, 48, 49, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-normal) var(--ease-bounce);
  animation: controls-enter var(--duration-slow) var(--ease-mechanical) forwards;
  animation-delay: 1.6s;
  opacity: 0;
}

.agent-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 28px rgba(214, 48, 49, 0.45);
}

.agent-fab:active {
  transform: scale(0.95);
}

.agent-fab.hidden {
  transform: scale(0);
  opacity: 0;
  pointer-events: none;
}

@keyframes controls-enter {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
