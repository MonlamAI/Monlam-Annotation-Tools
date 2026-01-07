import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')

  async function login(credentials) {
    try {
      const response = await api.post('/auth/token/', credentials)
      token.value = response.data.access
      refreshToken.value = response.data.refresh
      localStorage.setItem('token', token.value)
      localStorage.setItem('refreshToken', refreshToken.value)
      await fetchUser()
      return { success: true }
    } catch (error) {
      console.error('Login failed:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      }
    }
  }

  async function logout() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  async function fetchUser() {
    try {
      const response = await api.get('/auth/me/')
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      if (error.response?.status === 401) {
        await logout()
      }
    }
  }

  async function refreshAccessToken() {
    try {
      const response = await api.post('/auth/token/refresh/', {
        refresh: refreshToken.value
      })
      token.value = response.data.access
      localStorage.setItem('token', token.value)
      return true
    } catch (error) {
      await logout()
      return false
    }
  }

  // Initialize user if token exists
  if (token.value) {
    fetchUser()
  }

  return {
    user,
    token,
    isAuthenticated,
    username,
    login,
    logout,
    fetchUser,
    refreshAccessToken
  }
})

