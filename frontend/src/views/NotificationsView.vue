<template>
  <div class="animate-fade-in">
    <div class="card">
      <div class="card-title">
        Новые объявления из мониторинга
        <button class="btn-delete-all" @click="clearAllNotifications" v-if="notificationSessions.length > 0">
          Очистить все
        </button>
      </div>
      
      <div class="notifications-sessions-list" v-if="notificationSessions.length > 0">
        <div 
          v-for="session in notificationSessions" 
          :key="session.session_id"
          class="notification-session-item"
          :class="{ expanded: expandedSessions[session.session_id] }"
        >
          <div class="notification-session-header" @click="toggleSession(session.session_id)">
            <div class="notification-session-info">
              <div class="notification-session-query">{{ session.search_query }}</div>
              <div class="notification-session-meta">
                {{ session.city }} • 
                <span :class="{ 'has-unread': getUnreadCount(session) > 0 }">
                  Всего объявлений: {{ session.count }}
                  <span v-if="getUnreadCount(session) > 0" class="unread-badge">
                    {{ getUnreadCount(session) }} непрочитанных
                  </span>
                </span>
              </div>
            </div>
            <div class="notification-session-actions" @click.stop>
              <button class="btn-delete-session" @click="clearSessionNotifications(session.session_id)">
                Удалить все
              </button>
            </div>
          </div>
          
          <div class="notification-session-results" v-if="expandedSessions[session.session_id]">
            <div class="ad-list">
              <div 
                v-for="ad in session.notifications" 
                :key="ad.id" 
                class="ad-item"
                :class="{ 'is-read': ad.is_read }"
              >
                <button class="btn-delete-notification" @click="deleteNotification(ad.id)">
                  Удалить
                </button>
                <div class="ad-title">{{ ad.title }}</div>
                <div class="ad-price">{{ ad.price }}</div>
                <div class="ad-meta">{{ ad.location }}</div>
                <div class="ad-meta">{{ ad.date }}</div>
                <div class="ad-meta" v-if="ad.link">
                  <a :href="ad.link" target="_blank" class="ad-link" rel="noopener noreferrer">
                    Открыть на Avito
                  </a>
                </div>
                <div class="ad-meta">{{ formatDate(ad.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-history">
        Нет новых объявлений
        <br>
        <small>Запустите мониторинг, чтобы получать уведомления о новых объявлениях</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useToastStore } from '@/stores/toast'
import { useFormatters } from '@/composables/useFormatters'

const emit = defineEmits(['updateCount'])

const toastStore = useToastStore()
const { formatDate } = useFormatters()

const notificationSessions = ref([])
const expandedSessions = ref({})
let interval = null

const getUnreadCount = (session) => {
  const notifications = session.notifications || []
  return notifications.filter(n => !n.is_read).length
}

const loadNotifications = async () => {
  try {
    const response = await fetch('/api/notifications')
    const data = await response.json()
    
    const sessions = data.sessions || []
    let totalUnread = 0
    
    for (const session of sessions) {
      const notifications = session.notifications || []
      const unreadCount = notifications.filter(n => !n.is_read).length
      session.unread_count = unreadCount
      totalUnread += unreadCount
    }
    
    notificationSessions.value = sessions
    emit('updateCount', totalUnread)
  } catch (error) {
    console.error('Error loading notifications:', error)
  }
}

const toggleSession = async (sessionId) => {
  const wasExpanded = expandedSessions.value[sessionId]
  
  if (wasExpanded) {
    expandedSessions.value[sessionId] = false
  } else {
    expandedSessions.value[sessionId] = true
    
    const session = notificationSessions.value.find(s => s.session_id === sessionId)
    if (session && getUnreadCount(session) > 0) {
      await markSessionAsRead(sessionId)
    }
  }
}

const markSessionAsRead = async (sessionId) => {
  try {
    const response = await fetch(`/api/notifications/mark-session-read/${sessionId}`, {
      method: 'POST'
    })
    const data = await response.json()
    if (data.success) {
      const session = notificationSessions.value.find(s => s.session_id === sessionId)
      if (session) {
        for (const ad of session.notifications) {
          ad.is_read = true
        }
        session.unread_count = 0
      }
      let totalUnread = 0
      for (const s of notificationSessions.value) {
        totalUnread += s.unread_count || 0
      }
      emit('updateCount', totalUnread)
    }
  } catch (error) {
    console.error('Error marking session as read:', error)
  }
}

const deleteNotification = async (notificationId) => {
  try {
    const response = await fetch(`/api/notifications/delete/${notificationId}`, { method: 'DELETE' })
    const data = await response.json()
    if (data.success) {
      await loadNotifications()
      toastStore.addToast('Уведомление удалено', 'success')
    }
  } catch (error) {
    toastStore.addToast('Ошибка удаления', 'error')
  }
}

const clearSessionNotifications = async (sessionId) => {
  if (!confirm('Удалить все уведомления этой сессии?')) return
  
  try {
    const response = await fetch(`/api/notifications/clear-session/${sessionId}`, { method: 'DELETE' })
    const data = await response.json()
    if (data.success) {
      await loadNotifications()
      toastStore.addToast('Уведомления сессии удалены', 'success')
    }
  } catch (error) {
    toastStore.addToast('Ошибка удаления', 'error')
  }
}

const clearAllNotifications = async () => {
  if (!confirm('Очистить все уведомления?')) return
  
  try {
    await fetch('/api/notifications/clear', { method: 'POST' })
    notificationSessions.value = []
    expandedSessions.value = {}
    emit('updateCount', 0)
    toastStore.addToast('Уведомления очищены', 'success')
  } catch (error) {
    toastStore.addToast('Ошибка очистки', 'error')
  }
}

onMounted(() => {
  loadNotifications()
  interval = setInterval(loadNotifications, 15000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<style scoped>
.card {
  border: 1px solid #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  background: #0d0d0d;
}

body.light-theme .card {
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

.btn-delete-all {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-delete-all:hover {
  background: #2563eb;
}

.notification-session-item {
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

body.light-theme .notification-session-item {
  border-color: #e2e8f0;
}

.notification-session-header {
  padding: 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: #121212;
}

body.light-theme .notification-session-header {
  background: #f0f0f0;
}

.notification-session-header:hover {
  background: #1a1a1a;
}

body.light-theme .notification-session-header:hover {
  background: #e5e5e5;
}

.notification-session-query {
  font-weight: 600;
  font-size: 14px;
}

.notification-session-meta {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.notification-session-meta .has-unread {
  color: #3b82f6;
}

.unread-badge {
  display: inline-block;
  background: #3b82f6;
  color: white;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  font-weight: 600;
}

.btn-delete-session {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-delete-session:hover {
  background: #2563eb;
}

.notification-session-results {
  padding: 16px;
  border-top: 1px solid #1f1f1f;
}

body.light-theme .notification-session-results {
  border-top-color: #e2e8f0;
}

.ad-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ad-item {
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 16px;
  position: relative;
  background: #111111;
}

.ad-item.is-read {
  opacity: 1;
}

body.light-theme .ad-item {
  border-color: #e2e8f0;
  background: white;
}

.ad-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  padding-right: 80px;
}

.ad-price {
  font-size: 18px;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 8px;
}

.ad-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #9ca3af;
  flex-wrap: wrap;
}

.ad-link {
  color: #3b82f6;
  text-decoration: none;
}

.ad-link:hover {
  text-decoration: underline;
}

.btn-delete-notification {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 11px;
  position: absolute;
  top: 12px;
  right: 12px;
  font-weight: 600;
}

.btn-delete-notification:hover {
  background: #2563eb;
}

.empty-history {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}
</style>