<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '../../stores/userStore'

const emit = defineEmits<{ (e: 'close'): void }>()
const userStore = useUserStore()

const mode = ref<'login' | 'register'>('login')
const form = reactive({ username: '', password: '' })
const error = ref<string | null>(null)

async function submit() {
  error.value = null
  if (form.username.length < 3) { error.value = '用户名至少 3 个字符'; return }
  if (form.password.length < 6) { error.value = '密码至少 6 个字符'; return }

  const err = mode.value === 'login'
    ? await userStore.login(form.username, form.password)
    : await userStore.register(form.username, form.password)

  if (err) { error.value = err; return }
  emit('close')
}

function switchMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  error.value = null
}
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('close')">
      <div class="modal-card">
        <!-- Header -->
        <div class="modal-header">
          <h2 class="modal-title">{{ mode === 'login' ? '登录' : '注册' }}</h2>
          <button class="modal-close" @click="emit('close')">&times;</button>
        </div>

        <!-- Form -->
        <form class="modal-body" @submit.prevent="submit">
          <div class="field">
            <label class="field-label">用户名</label>
            <input
              v-model="form.username"
              type="text"
              class="field-input"
              placeholder="输入用户名"
              autocomplete="username"
              minlength="3"
            />
          </div>
          <div class="field">
            <label class="field-label">密码</label>
            <input
              v-model="form.password"
              type="password"
              class="field-input"
              placeholder="输入密码"
              autocomplete="current-password"
              minlength="6"
            />
          </div>

          <div v-if="error" class="error-msg">{{ error }}</div>

          <button
            type="submit"
            class="submit-btn"
            :disabled="userStore.loading"
          >
            {{ userStore.loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
          </button>
        </form>

        <!-- Footer -->
        <div class="modal-footer">
          <button class="switch-link" @click="switchMode">
            {{ mode === 'login' ? '没有账号？注册' : '已有账号？登录' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 600;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: overlay-in 0.15s ease;
}

@keyframes overlay-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-card {
  width: 360px;
  max-width: calc(100vw - 32px);
  background: var(--glass-bg-active);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  animation: card-in 0.2s var(--ease-signal);
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(8px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-5) 0;
}

.modal-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.modal-close {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  font-size: 20px;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-close:hover { background: var(--border-light); color: var(--text-primary); }

/* Body */
.modal-body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field { display: flex; flex-direction: column; gap: 6px; }

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
}

.field-input {
  height: 40px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--surface-map);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color var(--duration-fast);
}
.field-input:focus { border-color: var(--signal-blue); }

.error-msg {
  font-size: var(--text-xs);
  color: var(--signal-red);
  padding: var(--space-2) var(--space-3);
  background: rgba(214, 48, 49, 0.08);
  border-radius: var(--radius-sm);
}

.submit-btn {
  height: 42px;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--signal-red), var(--signal-amber));
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--duration-fast);
}
.submit-btn:hover { opacity: 0.9; }
.submit-btn:disabled { opacity: 0.5; cursor: default; }

/* Footer */
.modal-footer {
  padding: 0 var(--space-5) var(--space-4);
  text-align: center;
}

.switch-link {
  border: none;
  background: none;
  font-size: var(--text-xs);
  color: var(--signal-blue);
  cursor: pointer;
}
.switch-link:hover { text-decoration: underline; }
</style>
