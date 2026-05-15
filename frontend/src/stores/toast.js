import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const notifications = ref([])
  
  const addToast = (message, type = 'info') => {
    const id = Date.now()
    notifications.value.push({ id, message, type })
    
    setTimeout(() => {
      notifications.value = notifications.value.filter(n => n.id !== id)
    }, 5000)
  }
  
  const removeToast = (id) => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }
  
  return {
    notifications,
    addToast,
    removeToast
  }
})