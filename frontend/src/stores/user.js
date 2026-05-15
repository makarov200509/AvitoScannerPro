import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useToastStore } from './toast'

export const useUserStore = defineStore('user', () => {
  const toastStore = useToastStore()
  
  const stats = ref({
    searches_count: 0,
    ads_found: 0,
    monitoring_sessions: 0,
    active_processes: 0
  })
  
  const maxProcesses = ref(7)
  const loading = ref(false)
  
  const fetchStats = async () => {
    loading.value = true
    try {
      const response = await fetch('/api/user/stats')
      const data = await response.json()
      stats.value = {
        searches_count: data.searches_count || 0,
        ads_found: data.ads_found || 0,
        monitoring_sessions: data.monitoring_sessions || 0,
        active_processes: data.active_processes || 0
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      loading.value = false
    }
  }
  
  const fetchActiveProcesses = async () => {
    try {
      const response = await fetch('/api/active-processes')
      const data = await response.json()
      stats.value.active_processes = (data.processes || []).length
      return data.processes || []
    } catch (error) {
      console.error('Error fetching processes:', error)
      return []
    }
  }
  
  const stopProcess = async (processId) => {
    try {
      const response = await fetch(`/api/process/stop/${processId}`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        toastStore.addToast(data.message, 'success')
        await fetchActiveProcesses()
        await fetchStats()
        return true
      }
      return false
    } catch (error) {
      toastStore.addToast('Ошибка остановки процесса', 'error')
      return false
    }
  }
  
  const stopAllProcesses = async () => {
    try {
      const response = await fetch('/api/process/stop-all', { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        toastStore.addToast(`Остановлено ${data.stopped_count} процессов`, 'success')
        await fetchActiveProcesses()
        await fetchStats()
        return true
      }
      return false
    } catch (error) {
      toastStore.addToast('Ошибка остановки процессов', 'error')
      return false
    }
  }
  
  return {
    stats,
    maxProcesses,
    loading,
    fetchStats,
    fetchActiveProcesses,
    stopProcess,
    stopAllProcesses
  }
})