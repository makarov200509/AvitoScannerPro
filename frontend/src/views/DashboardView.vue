<template>
  <div class="container">
    <TheHeader 
      @showChangePassword="showChangePasswordModal = true"
      @showDeleteAccount="showDeleteAccountModal = true"
      @showHelp="showHelpModal = true"
    />
    
    <HelpModal v-model:visible="showHelpModal" />
    
    <StatsCards />
    
    <ActiveProcesses />
    
    <div class="tabs animate-fade-in">
      <div 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]" 
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.key === 'notifications' && totalUnreadCount > 0" class="notification-badge">
          {{ totalUnreadCount > 99 ? '99+' : totalUnreadCount }}
        </span>
      </div>
    </div>
    
    <SearchView v-if="activeTab === 'search'" />
    <HistoryView v-if="activeTab === 'history'" />
    <MonitoringView v-if="activeTab === 'monitoring'" />
    <NotificationsView 
      v-if="activeTab === 'notifications'" 
      @update-count="updateUnreadCount"
      ref="notificationsViewRef"
    />
    <AnalysisView v-if="activeTab === 'analysis'" />
    <AnalysisHistoryView v-if="activeTab === 'analysisHistory'" />
    
    <ChangePasswordModal 
      :visible="showChangePasswordModal"
      @update:visible="showChangePasswordModal = $event"
    />
    
    <DeleteAccountModal 
      :visible="showDeleteAccountModal"
      @update:visible="showDeleteAccountModal = $event"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useResellerStore } from '@/stores/reseller'
import TheHeader from '@/components/TheHeader.vue'
import HelpModal from '@/components/HelpModal.vue'
import StatsCards from '@/components/StatsCards.vue'
import ActiveProcesses from '@/components/ActiveProcesses.vue'
import ChangePasswordModal from '@/components/ChangePasswordModal.vue'
import DeleteAccountModal from '@/components/DeleteAccountModal.vue'
import SearchView from './SearchView.vue'
import HistoryView from './HistoryView.vue'
import MonitoringView from './MonitoringView.vue'
import NotificationsView from './NotificationsView.vue'
import AnalysisView from './AnalysisView.vue'
import AnalysisHistoryView from './AnalysisHistoryView.vue'

const authStore = useAuthStore()
const userStore = useUserStore()
const resellerStore = useResellerStore()

const activeTab = ref('search')
const showChangePasswordModal = ref(false)
const showDeleteAccountModal = ref(false)
const showHelpModal = ref(false)
const totalUnreadCount = ref(0)
let unreadPollInterval = null

const tabs = [
  { key: 'search', label: 'Новый поиск' },
  { key: 'history', label: 'История поисков' },
  { key: 'monitoring', label: 'Мониторинг' },
  { key: 'notifications', label: 'Уведомления' },
  { key: 'analysis', label: 'Анализ рынка' },
  { key: 'analysisHistory', label: 'История анализов' }
]

const updateUnreadCount = (count) => {
  totalUnreadCount.value = count
}

const fetchUnreadCount = async () => {
  try {
    const response = await fetch('/api/notifications')
    const data = await response.json()
    const sessions = data.sessions || []
    let totalUnread = 0
    for (const session of sessions) {
      const notifications = session.notifications || []
      totalUnread += notifications.filter(n => !n.is_read).length
    }
    totalUnreadCount.value = totalUnread
  } catch (error) {
    console.error('Error fetching unread count:', error)
  }
}

onMounted(async () => {
  await authStore.checkAuth()
  await userStore.fetchStats()
  resellerStore.init()
  
  fetchUnreadCount()
  unreadPollInterval = setInterval(fetchUnreadCount, 15000)
})

onUnmounted(() => {
  if (unreadPollInterval) {
    clearInterval(unreadPollInterval)
  }
})
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  border-bottom: 1px solid #1f1f1f;
  padding-bottom: 12px;
  flex-wrap: wrap;
}

body.light-theme .tabs {
  border-bottom-color: #e2e8f0;
}

.tab {
  padding: 8px 16px;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #9ca3af;
  position: relative;
}

body.light-theme .tab {
  color: #4a5568;
}

.tab.active {
  background: #121212;
  color: #3b82f6;
}

body.light-theme .tab.active {
  background: #f0f0f0;
  color: #3b82f6;
}

.notification-badge {
  display: inline-block;
  background: #3b82f6;
  color: white;
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 10px;
  margin-left: 8px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .container {
    padding: 12px;
  }
  
  .tabs {
    gap: 6px;
    margin-bottom: 16px;
    padding-bottom: 8px;
  }
  
  .tab {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .notification-badge {
    font-size: 9px;
    padding: 1px 5px;
    margin-left: 4px;
  }
}
</style>