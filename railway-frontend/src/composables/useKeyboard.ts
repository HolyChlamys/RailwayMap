import { onMounted, onUnmounted } from 'vue'
import { useSearchStore } from '../stores/searchStore'

export function useKeyboard() {
  const searchStore = useSearchStore()

  function handleKeydown(e: KeyboardEvent) {
    // ⌘K / Ctrl+K → focus search
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      searchStore.openDropdown()
      // Focus the search input (handled by SearchBar's ref)
      const input = document.querySelector('.search-input') as HTMLInputElement | null
      input?.focus()
    }

    // Escape → close dropdown
    if (e.key === 'Escape') {
      searchStore.closeDropdown()
    }
  }

  onMounted(() => document.addEventListener('keydown', handleKeydown))
  onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
}
