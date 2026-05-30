<template>
  <div class="stats-section" :class="{ closed: !displayStore.statsVisible }">
    <div class="stats-header">
      <div class="stats-title">Статистика использования</div>
      <button class="btn-secondary btn-sm" @click="refreshData" :disabled="userStore.loading">
        {{ userStore.loading ? 'Обновление...' : 'Обновить' }}
      </button>
    </div>
    <div class="stats-grid-large">
      <div class="stat-card-large">
        <div class="stat-label">Поисковые запросы</div>
        <div class="stat-value">{{ userStore.stats.searches_count || 0 }}</div>
        <div class="stat-sub">Всего выполнено</div>
      </div>
      <div class="stat-card-large">
        <div class="stat-label">Найдено объявлений</div>
        <div class="stat-value">{{ formatNumber(userStore.stats.ads_found || 0) }}</div>
        <div class="stat-sub">За всё время</div>
      </div>
      <div class="stat-card-large">
        <div class="stat-label">Активные процессы</div>
        <div class="stat-value">{{ userStore.stats.active_processes || 0 }} / {{ userStore.maxProcesses }}</div>
        <div class="stat-sub">Максимум {{ userStore.maxProcesses }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { useDisplayStore } from '@/stores/display'
import { useToastStore } from '@/stores/toast'

const userStore = useUserStore()
const displayStore = useDisplayStore()
const toastStore = useToastStore()

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(0) + 'K'
  return num.toString()
}

const refreshData = async () => {
  await userStore.fetchStats()
  toastStore.addToast('Данные обновлены', 'success')
}
</script>

<style scoped>
.stats-section {
  border: 1px solid #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 28px;
  background: #0d0d0d;
}

body.light-theme .stats-section {
  border-color: #e2e8f0;
  background: white;
}

.stats-section.closed {
  display: none;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-title {
  font-size: 16px;
  font-weight: 600;
}

.stats-grid-large {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card-large {
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border: 1px solid #1f1f1f;
  background: #111111;
}

body.light-theme .stat-card-large {
  background: #fafafa;
  border-color: #e2e8f0;
}

.stat-label {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 8px;
}

body.light-theme .stat-label {
  color: #4a5568;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #3b82f6;
}

.stat-sub {
  font-size: 11px;
  color: #6b7280;
  margin-top: 6px;
}

.btn-secondary {
  border: 1px solid #2a2a2a;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  background: #121212;
  color: #e2e8f0;
}

body.light-theme .btn-secondary {
  background: #f0f0f0;
  border-color: #e2e8f0;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #1a1a1a;
}

body.light-theme .btn-secondary:hover {
  background: #e5e5e5;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .stats-grid-large {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  
  .stat-card-large {
    padding: 8px 12px !important;
  }
  
  .stat-value {
    font-size: 18px !important;
  }
  
  .stat-label {
    font-size: 11px !important;
  }
  
  .btn-sm {
    padding: 4px 8px !important;
    font-size: 10px !important;
  }
}
</style>