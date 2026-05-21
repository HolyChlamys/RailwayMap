<script setup lang="ts">
import type { ChatMessage } from '../../types/agent'
import AgentRouteCard from './AgentRouteCard.vue'

defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  navigate: [type: string, action: string]
}>()

function formatText(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/•/g, '<span class="bullet">•</span>')
}
</script>

<template>
  <div class="bubble-wrapper" :class="message.role">
    <div v-if="message.role === 'agent'" class="bubble-avatar">🤖</div>

    <div class="bubble-content">
      <div class="bubble-text" v-html="formatText(message.content.text)" />

      <!-- Route plan cards -->
      <AgentRouteCard
        v-for="plan in message.content.routePlans"
        :key="plan.id"
        :plan="plan"
        @navigate="(t, a) => emit('navigate', t, a)"
      />

      <div class="bubble-time">
        {{ message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
      </div>
    </div>

    <div v-if="message.role === 'user'" class="bubble-avatar user-avatar">我</div>
  </div>
</template>

<style scoped>
.bubble-wrapper {
  display: flex;
  gap: var(--space-2);
  max-width: 88%;
  animation: bubble-in var(--duration-normal) var(--ease-signal);
}

@keyframes bubble-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.bubble-wrapper.agent {
  align-self: flex-start;
}

.bubble-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.bubble-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, var(--text-secondary), var(--text-primary));
  color: white;
  font-size: 11px;
  font-weight: 600;
}

.bubble-content {
  min-width: 0;
}

.bubble-text {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  line-height: 1.65;
  word-break: break-word;
}

.bubble-wrapper.agent .bubble-text {
  background: var(--border-light);
  color: var(--text-primary);
  border-top-left-radius: var(--radius-xs);
}

.bubble-wrapper.user .bubble-text {
  background: var(--signal-blue);
  color: white;
  border-top-right-radius: var(--radius-xs);
}

.bubble-text :deep(strong) {
  font-weight: 600;
}

.bubble-text :deep(.bullet) {
  color: var(--signal-red);
  margin-right: 2px;
}

.bubble-time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-tertiary);
  margin-top: 2px;
  padding: 0 var(--space-1);
}

.bubble-wrapper.user .bubble-time {
  text-align: right;
}
</style>
