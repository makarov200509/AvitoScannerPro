import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDisplayStore = defineStore('display', () => {
  const statsVisible = ref(true)
  const qrVisible = ref(false)
  
  const toggleStatsVisible = () => {
    statsVisible.value = !statsVisible.value
  }
  
  const toggleQrVisible = () => {
    qrVisible.value = !qrVisible.value
  }
  
  const setQrVisible = (value) => {
    qrVisible.value = value
  }
  
  return {
    statsVisible,
    qrVisible,
    toggleStatsVisible,
    toggleQrVisible,
    setQrVisible
  }
})