import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useResellerStore = defineStore('reseller', () => {
  const isActive = ref(false)
  
  const init = () => {
    const saved = localStorage.getItem('resellerMode')
    isActive.value = saved === 'true'
  }
  
  const toggle = () => {
    isActive.value = !isActive.value
    localStorage.setItem('resellerMode', isActive.value)
  }
  
  return {
    isActive,
    init,
    toggle
  }
})