import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/authApi'
import { favoriteApi, type FavoriteItem } from '../api/favoriteApi'

const TOKEN_KEY = 'railwaymap_token'
const USER_KEY = 'railwaymap_user'

function loadToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function loadUsername(): string | null {
  return localStorage.getItem(USER_KEY)
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(loadToken())
  const username = ref<string | null>(loadUsername())
  const loading = ref(false)
  const favorites = ref<FavoriteItem[]>([])
  const favSet = computed(() => new Set(favorites.value.map(f => `${f.type}:${f.target_id}`)))

  const isLoggedIn = computed(() => !!token.value)

  async function login(user: string, password: string): Promise<string | null> {
    loading.value = true
    try {
      const res = await authApi.login(user, password)
      if (res.success && res.token) {
        token.value = res.token
        username.value = user
        localStorage.setItem(TOKEN_KEY, res.token)
        localStorage.setItem(USER_KEY, user)
        return null
      }
      return res.message || '登录失败'
    } catch (e: any) {
      return e.message || '网络错误'
    } finally {
      loading.value = false
    }
  }

  async function register(user: string, password: string): Promise<string | null> {
    loading.value = true
    try {
      const res = await authApi.register(user, password)
      if (res.success && res.token) {
        token.value = res.token
        username.value = user
        localStorage.setItem(TOKEN_KEY, res.token)
        localStorage.setItem(USER_KEY, user)
        return null
      }
      return res.message || '注册失败'
    } catch (e: any) {
      return e.message || '网络错误'
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    username.value = null
    favorites.value = []
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  // ---- Favorites ----
  async function loadFavorites() {
    if (!isLoggedIn.value) return
    try {
      favorites.value = await favoriteApi.getAll()
    } catch { /* ignore */ }
  }

  function isFavorite(type: string, targetId: string): boolean {
    return favSet.value.has(`${type}:${targetId}`)
  }

  async function toggleFavorite(type: string, targetId: string, label: string, data?: Record<string, any>) {
    if (!isLoggedIn.value) return
    try {
      const existing = favorites.value.find(f => f.type === type && f.target_id === targetId)
      if (existing) {
        await favoriteApi.remove(existing.id)
        favorites.value = favorites.value.filter(f => f.id !== existing.id)
      } else {
        await favoriteApi.add(type, targetId, label, data)
        // Re-fetch to get the server-assigned ID
        await loadFavorites()
      }
    } catch { /* ignore */ }
  }

  function getToken(): string | null {
    return token.value || loadToken()
  }

  return { token, username, loading, favorites, favSet, isLoggedIn, login, register, logout, loadFavorites, isFavorite, toggleFavorite, getToken }
})
