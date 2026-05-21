<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useAgentStore } from '../../stores/agentStore'
import { useAgentChat } from '../../composables/useAgentChat'
import AgentBubble from './AgentBubble.vue'

const agentStore = useAgentStore()
const { sendMessage } = useAgentChat()

const inputText = ref('')
const messagesEl = ref<HTMLElement | null>(null)

const emit = defineEmits<{
  navigate: [type: string, action: string]
}>()

// Auto-scroll to bottom when new messages arrive
watch(
  () => agentStore.messages.length,
  async () => {
    await nextTick()
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  },
)

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  sendMessage(text)
}

function handleQuickChip(prompt: string) {
  inputText.value = prompt
  handleSend()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <Transition name="panel-slide">
    <div v-if="agentStore.isOpen" class="agent-panel">
      <!-- Header -->
      <div class="panel-header">
        <div class="panel-title-group">
          <div class="panel-avatar">🤖</div>
          <div>
            <div class="panel-title">铁路助手</div>
            <div class="panel-status">
              <span class="status-dot" />
              在线
            </div>
          </div>
        </div>
        <div class="panel-header-actions">
          <button class="header-btn" title="清空对话" @click="agentStore.clearMessages()">
            ↺
          </button>
          <button class="header-btn" title="关闭" @click="agentStore.closePanel()">
            ✕
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="messagesEl" class="panel-messages">
        <!-- Welcome + quick suggestions (shown when only welcome msg exists) -->
        <div
          v-if="agentStore.messageCount === 1"
          class="quick-suggestions"
        >
          <button
            v-for="chip in agentStore.defaultQuickSuggestions"
            :key="chip.prompt"
            class="quick-chip"
            @click="handleQuickChip(chip.prompt)"
          >
            {{ chip.label }}
          </button>
        </div>

        <!-- Message bubbles -->
        <AgentBubble
          v-for="msg in agentStore.messages"
          :key="msg.id"
          :message="msg"
          @navigate="(t, a) => emit('navigate', t, a)"
        />

        <!-- Typing indicator -->
        <div v-if="agentStore.isProcessing" class="typing-indicator">
          <span /><span /><span />
        </div>
      </div>

      <!-- Input -->
      <div class="panel-input-area">
        <input
          v-model="inputText"
          type="text"
          class="chat-input"
          placeholder="输入你的问题…"
          @keydown="handleKeydown"
        />
        <button
          class="send-btn"
          :class="{ active: inputText.trim() }"
          @click="handleSend"
        >
          ↑
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.agent-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 350;
  width: 400px;
  max-width: 100vw;
  background: var(--glass-bg-active);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-left: 1px solid var(--border-light);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
}

/* Header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-light);
}

.panel-title-group {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.panel-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--signal-blue), var(--signal-red));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.panel-title {
  font-weight: 700;
  font-size: var(--font-base);
}

.panel-status {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--signal-green);
}

.panel-header-actions {
  display: flex;
  gap: var(--space-2);
}

.header-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: var(--border-light);
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all var(--duration-fast);
}
.header-btn:hover {
  background: var(--border-medium);
  color: var(--text-primary);
}

/* Messages */
.panel-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* Quick suggestions */
.quick-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
  padding-bottom: var(--space-2);
}

.quick-chip {
  padding: 6px 14px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-medium);
  background: var(--glass-bg-active);
  font-size: var(--text-sm);
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--duration-fast);
  font-family: inherit;
}
.quick-chip:hover {
  background: var(--border-light);
  border-color: var(--text-tertiary);
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: var(--space-2) var(--space-3);
  align-self: flex-start;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: typing-bounce 1.2s ease-in-out infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

/* Input */
.panel-input-area {
  flex-shrink: 0;
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: var(--space-2);
}

.chat-input {
  flex: 1;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-sm);
  padding: 10px var(--space-3);
  font-size: var(--text-base);
  font-family: inherit;
  outline: none;
  transition: border-color var(--duration-fast);
}
.chat-input:focus {
  border-color: var(--signal-blue);
}

.send-btn {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--border-light);
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast);
  font-size: 18px;
}
.send-btn.active {
  background: var(--signal-blue);
  color: white;
}
.send-btn.active:hover {
  filter: brightness(1.1);
}

/* Panel slide transition */
.panel-slide-enter-active {
  transition: transform var(--duration-slow) var(--ease-mechanical);
}
.panel-slide-leave-active {
  transition: transform 250ms var(--ease-mechanical);
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  transform: translateX(100%);
}

@media (max-width: 640px) {
  .agent-panel {
    width: 100vw;
    max-width: 100vw;
  }
}
</style>
