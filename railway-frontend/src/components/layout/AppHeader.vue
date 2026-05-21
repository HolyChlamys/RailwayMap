<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSearchStore, type SearchResultItem } from '../../stores/searchStore'
import { useStationStore } from '../../stores/stationStore'
import { useTrainStore } from '../../stores/trainStore'
import { useMapStore } from '../../stores/mapStore'
import { useUserStore } from '../../stores/userStore'
import SearchBar from '../search/SearchBar.vue'

const searchStore = useSearchStore()
const stationStore = useStationStore()
const trainStore = useTrainStore()
const mapStore = useMapStore()
const userStore = useUserStore()

const isDarkMode = ref(document.documentElement.classList.contains('dark'))

const emit = defineEmits<{
  'search-select': [item: SearchResultItem]
  'show-login': []
}>()

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('dark', isDarkMode.value)
}

function onSearchSelect(item: SearchResultItem) {
  if (item.type === 'station' && item.station) {
    stationStore.setCurrentStation(item.station.id)
    mapStore.setFocusStation(String(item.station.id))
  } else if (item.type === 'train' && item.train) {
    trainStore.setCurrentTrain(item.train.no)
    mapStore.setFocusTrain(item.train.no)
  } else if (item.type === 'city') {
    mapStore.setFocusCity(item.action)
  }
  emit('search-select', item)
}
</script>

<template>
  <header class="app-header">
    <!-- Brand -->
    <div class="header-brand">
      <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="4" />
        <line x1="12" y1="2" x2="12" y2="6" />
        <line x1="12" y1="18" x2="12" y2="22" />
        <line x1="2" y1="12" x2="6" y2="12" />
        <line x1="18" y1="12" x2="22" y2="12" />
      </svg>
      <span class="brand-text">铁路地图</span>
    </div>

    <!-- Search -->
    <div class="header-search">
      <SearchBar @select="onSearchSelect" />
    </div>

    <!-- Right actions -->
    <div class="header-actions">
      <button
        class="action-btn"
        :title="isDarkMode ? '浅色模式' : '深色模式'"
        @click="toggleDarkMode"
      >
        {{ isDarkMode ? '☀' : '☽' }}
      </button>

      <button class="action-btn" title="关于">
        ℹ
      </button>

      <div
        class="user-avatar"
        :title="userStore.isLoggedIn ? userStore.username ?? '已登录' : '登录'"
        @click="userStore.isLoggedIn ? userStore.logout() : emit('show-login')"
      >
        <svg v-if="!userStore.isLoggedIn" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 22c0-4.4 3.6-8 8-8s8 3.6 8 8" />
        </svg>
        <span v-else class="user-initial">{{ userStore.username?.charAt(0).toUpperCase() }}</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 500;
  height: var(--header-h);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 0 var(--space-6);
  background: var(--glass-bg-active);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
  opacity: 0;
  animation: header-enter var(--duration-slow) var(--ease-mechanical) forwards;
  animation-delay: 1.4s;
}

@keyframes header-enter {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Brand */
.header-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.brand-icon {
  width: 26px;
  height: 26px;
  color: var(--signal-red);
}

.brand-text {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--signal-red);
  letter-spacing: 1px;
}

/* Search */
.header-search {
  flex: 1;
  max-width: 520px;
}

/* Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
  flex-shrink: 0;
}

.action-btn {
  width: 34px;
  height: 34px;
  border: none;
  background: var(--border-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-signal);
}
.action-btn:hover {
  background: var(--border-medium);
  color: var(--text-primary);
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--signal-red), var(--signal-amber));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background var(--duration-fast);
}
.user-avatar:hover {
  opacity: 0.85;
}

.user-initial {
  font-size: 14px;
  font-weight: 700;
  font-family: var(--font-mono);
}

@media (max-width: 640px) {
  .app-header {
    padding: 0 var(--space-3);
    gap: var(--space-2);
  }

  .brand-text {
    display: none;
  }

  .header-search {
    max-width: none;
  }

  .action-btn {
    width: 30px;
    height: 30px;
    font-size: 14px;
  }

  .user-avatar {
    width: 30px;
    height: 30px;
  }
}
</style>
