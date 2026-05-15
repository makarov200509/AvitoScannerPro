import { defineStore } from 'pinia'
import { ref } from 'vue'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const user = ref(null)
  const loading = ref(false)
  const authChecked = ref(false) // Добавляем флаг проверки
  
  const checkAuth = async () => {
    try {
      const response = await fetch('/api/me')
      const data = await response.json()
      
      if (data.authenticated) {
        isAuthenticated.value = true
        user.value = data.user
      } else {
        isAuthenticated.value = false
        user.value = null
      }
    } catch (error) {
      isAuthenticated.value = false
      user.value = null
    } finally {
      authChecked.value = true // Проверка завершена
    }
  }
  
  const login = async (username, password) => {
    loading.value = true
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      
      const data = await response.json()
      
      if (response.ok && data.success) {
        isAuthenticated.value = true
        user.value = data.user
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Ошибка входа' }
      }
    } catch (error) {
      return { success: false, error: 'Ошибка соединения' }
    } finally {
      loading.value = false
    }
  }
  
  const register = async (username, password) => {
    loading.value = true
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      
      const data = await response.json()
      
      if (response.ok && data.success) {
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Ошибка регистрации' }
      }
    } catch (error) {
      return { success: false, error: 'Ошибка соединения' }
    } finally {
      loading.value = false
    }
  }
  
  const logout = async () => {
    await fetch('/api/logout', { method: 'POST' })
    isAuthenticated.value = false
    user.value = null
    router.push('/login')
  }
  
  // Запускаем проверку при создании store
  checkAuth()
  
  return {
    isAuthenticated,
    user,
    loading,
    authChecked,
    checkAuth,
    login,
    register,
    logout
  }
})