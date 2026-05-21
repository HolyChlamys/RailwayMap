<script setup lang="ts">
import { ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { useSearchStore, type SearchResultItem } from '../../stores/searchStore'
import SearchDropdown from './SearchDropdown.vue'

const searchStore = useSearchStore()

const emit = defineEmits<{
  select: [item: SearchResultItem]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const isFocused = ref(false)

const tabs = [
  { key: 'station' as const, label: '车站' },
  { key: 'train' as const, label: '车次' },
  { key: 'city' as const, label: '城市' },
]

// Close dropdown when clicking outside
onClickOutside(dropdownRef, () => {
  isFocused.value = false
  searchStore.closeDropdown()
}, { ignore: [inputRef] })

function onFocus() {
  isFocused.value = true
  searchStore.openDropdown()
}

function onInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  searchStore.setQuery(value)
  searchStore.openDropdown()
}

function onTabClick(tab: 'station' | 'train' | 'city') {
  searchStore.setTab(tab)
  inputRef.value?.focus()
  searchStore.openDropdown()
}

function onSelect(item: SearchResultItem) {
  isFocused.value = false
  searchStore.closeDropdown()
  searchStore.setQuery(item.label)
  emit('select', item)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    isFocused.value = false
    searchStore.closeDropdown()
    inputRef.value?.blur()
  }
}
</script>

<template>
  <div
    ref="dropdownRef"
    class="search-bar"
    :class="{ focused: isFocused }"
  >
    <div class="search-bar-inner">
      <!-- Tab toggles -->
      <div class="search-tabs" role="tablist">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          role="tab"
          class="search-tab"
          :class="{ active: searchStore.activeTab === tab.key }"
          @click="onTabClick(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Input -->
      <div class="search-input-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          ref="inputRef"
          type="text"
          class="search-input"
          :placeholder="searchStore.placeholder"
          :value="searchStore.query"
          autocomplete="off"
          @focus="onFocus"
          @input="onInput"
          @keydown="onKeydown"
        />
        <kbd class="search-shortcut">⌘K</kbd>
      </div>
    </div>

    <!-- Dropdown -->
    <div v-show="isFocused" class="search-dropdown-wrap">
      <SearchDropdown @select="onSelect" />
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  position: relative;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: background var(--duration-normal), box-shadow var(--duration-normal);
}
.search-bar.focused {
  background: var(--glass-bg-active);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-medium);
}

.search-bar-inner {
  display: flex;
  align-items: center;
  padding: 3px;
  height: 40px;
}

/* Tabs */
.search-tabs {
  display: flex;
  gap: 1px;
  background: var(--border-light);
  border-radius: var(--radius-sm);
  padding: 2px;
  flex-shrink: 0;
  height: 32px;
  margin-left: 2px;
}

.search-tab {
  padding: 4px 12px;
  border: none;
  background: transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-signal);
  white-space: nowrap;
  font-family: inherit;
}
.search-tab.active {
  background: var(--glass-bg-active);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}
.search-tab:hover:not(.active) {
  color: var(--text-primary);
}

/* Input */
.search-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 var(--space-3);
  min-width: 0;
}

.search-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
  margin-right: var(--space-2);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: var(--text-base);
  color: var(--text-primary);
  font-family: inherit;
  min-width: 0;
}
.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-shortcut { display: none; /* hidden */
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--border-light);
  padding: 2px 7px;
  border-radius: var(--radius-sm);
}

/* Dropdown */
.search-dropdown-wrap {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--glass-bg-active);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 10;
  max-height: 360px;
  overflow-y: auto;
}

@media (max-width: 640px) {
  .search-shortcut { display: none; /* hidden */
    display: none;
  }

  .search-tab {
    padding: 4px 8px;
    font-size: 10px;
  }
}
</style>
