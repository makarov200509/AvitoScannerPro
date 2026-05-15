<template>
  <div class="active-processes" v-if="processes.length > 0">
    <div class="card-title" style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
      <span>Активные процессы ({{ processes.length }}/{{ userStore.maxProcesses }})</span>
      <button class="btn-stop-all" @click="handleStopAll">Остановить все</button>
    </div>
    <div class="processes-list">
      <div v-for="proc in processes" :key="proc.id" class="process-item">
        <div class="process-info">
          <div class="process-name">
            {{ getProcessType(proc.type) }}: {{ proc.query }}
          </div>
          <div class="process-details">
            {{ proc.city }} • Запущен: {{ formatTime(proc.startedAt) }}
          </div>
          <div class="process-status" v-if="proc.type === 'monitoring' && proc.endTime">
            Осталось: {{ formatTimeLeft(proc) }}
          </div>
        </div>
        <button class="btn-stop" @click="handleStop(proc.id)">Остановить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useToastStore } from '@/stores/toast'

const userStore = useUserStore()
const toastStore = useToastStore()

const processes = ref([])
let interval = null

const loadProcesses = async () => {
  processes.value = await userStore.fetchActiveProcesses()
}

const getProcessType = (type) => {
  const types = {
    search: 'Поиск',
    monitoring: 'Мониторинг',
    analysis: 'Анализ'
  }
  return types[type] || type
}

const formatTime = (timestamp) => {
  if (!timestamp) return '—'
  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return '—'
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return '—'
  }
}

const formatTimeLeft = (proc) => {
  if (!proc.endTime) return '—'
  try {
    const end = new Date(proc.endTime)
    if (isNaN(end.getTime())) return '—'
    const left = Math.max(0, Math.floor((end - Date.now()) / 60000))
    if (left <= 0) return 'Завершается'
    if (left < 60) return left + ' мин'
    const hours = Math.floor(left / 60)
    const minutes = left % 60
    return minutes > 0 ? hours + ' ч ' + minutes + ' мин' : hours + ' ч'
  } catch {
    return '—'
  }
}

const handleStop = async (processId) => {
  await userStore.stopProcess(processId)
  await loadProcesses()
}

const handleStopAll = async () => {
  if (!confirm(`Остановить все активные процессы (${processes.value.length})?`)) return
  await userStore.stopAllProcesses()
  await loadProcesses()
}

onMounted(() => {
  loadProcesses()
  interval = setInterval(loadProcesses, 10000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<style scoped>
.active-processes {
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 28px;
  border: 1px solid;
  background: inherit;
  border-color: #1a1a1a;
}

body.light-theme .active-processes {
  border-color: #e2e8f0;
  background: white;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.processes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.process-item {
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  border-left: 3px solid #eab308;
  background: #111111;
  border-color: #1f1f1f;
}

body.light-theme .process-item {
  background: #fafafa;
  border-color: #e2e8f0;
}

.process-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.process-name {
  font-weight: 600;
  font-size: 14px;
}

.process-details {
  font-size: 12px;
  color: #9ca3af;
}

.process-status {
  font-size: 12px;
  color: #eab308;
}

.btn-stop, .btn-stop-all {
  background: #eab308;
  color: #1a1a1a;
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-stop:hover, .btn-stop-all:hover {
  background: #ca8a04;
}
</style>