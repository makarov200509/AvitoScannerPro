import { defineStore } from 'pinia'
import { ref } from 'vue'

const escapeHtml = (text) => {
  if (!text) return ''
  const div = document.createElement('div')
  div.textContent = String(text)
  return div.innerHTML
}

export const useToastStore = defineStore('toast', () => {
  const notifications = ref([])
  
  const addToast = (message, type = 'info') => {
    const id = Date.now()
    const safeMessage = escapeHtml(message)
    notifications.value.push({ id, message: safeMessage, type })
    
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