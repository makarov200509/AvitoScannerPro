<template>
  <div class="animate-fade-in">
    <div class="card">
      <div class="card-title">
        История поисков
        <button class="btn-delete-all" @click="clearAllHistory" v-if="searchHistory.length > 0">
          Удалить все
        </button>
      </div>
      
      <div class="search-history-list" v-if="searchHistory.length > 0">
        <div 
          v-for="item in searchHistory" 
          :key="item.session_id" 
          class="search-history-item"
          :class="{ expanded: expandedSessions[item.session_id] }"
        >
          <div class="search-history-header" @click="toggleSession(item.session_id)">
            <div class="search-info">
              <div class="search-query">{{ item.search_query }}</div>
              <div class="search-meta">
                {{ item.city }} • Найдено: {{ item.results_count }} • {{ formatDate(item.created_at) }}
                <span v-if="item.min_price || item.max_price" class="search-meta-price">
                  • Цена: {{ item.min_price ? formatPriceNum(item.min_price) : 'Любая' }} - 
                  {{ item.max_price ? formatPriceNum(item.max_price) : 'Любая' }}
                </span>
              </div>
            </div>
            <div class="search-actions" @click.stop>
              <button class="btn-delete" @click="deleteSession(item.session_id)">Удалить</button>
            </div>
          </div>
          
          <div class="search-results" v-if="expandedSessions[item.session_id]">
            <div class="ad-list" v-if="sessionResults[item.session_id]">
              <AdCard 
                v-for="(ad, idx) in sessionResults[item.session_id]" 
                :key="ad.ad_id"
                :ad="ad"
                :index="idx + 1"
              />
            </div>
            <div v-else class="loading-results">Загрузка результатов...</div>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-history">
        История поисков пуста
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '@/stores/toast'
import { useFormatters } from '@/composables/useFormatters'
import AdCard from '@/components/AdCard.vue'

const toastStore = useToastStore()
const { formatDate, formatPriceNum } = useFormatters()

const searchHistory = ref([])
const expandedSessions = ref({})
const sessionResults = ref({})

const loadHistory = async () => {
  try {
    const response = await fetch('/api/search-history')
    const data = await response.json()
    searchHistory.value = data.history || []
  } catch (error) {
    console.error('Error loading history:', error)
  }
}

const toggleSession = async (sessionId) => {
  if (expandedSessions.value[sessionId]) {
    expandedSessions.value[sessionId] = false
  } else {
    expandedSessions.value[sessionId] = true
    if (!sessionResults.value[sessionId]) {
      await loadSessionResults(sessionId)
    }
  }
}

const loadSessionResults = async (sessionId) => {
  try {
    const response = await fetch(`/api/search-history/${sessionId}/results`)
    const data = await response.json()
    sessionResults.value[sessionId] = data.results || []
  } catch (error) {
    sessionResults.value[sessionId] = []
  }
}

const deleteSession = async (sessionId) => {
  if (!confirm('Удалить эту историю поиска?')) return
  
  try {
    await fetch(`/api/search-history/${sessionId}`, { method: 'DELETE' })
    searchHistory.value = searchHistory.value.filter(h => h.session_id !== sessionId)
    delete expandedSessions.value[sessionId]
    delete sessionResults.value[sessionId]
    toastStore.addToast('История удалена', 'success')
  } catch (error) {
    toastStore.addToast('Ошибка удаления', 'error')
  }
}

const clearAllHistory = async () => {
  if (!confirm('Удалить ВСЮ историю поисков?')) return
  
  for (const item of searchHistory.value) {
    try {
      await fetch(`/api/search-history/${item.session_id}`, { method: 'DELETE' })
    } catch (error) {}
  }
  
  searchHistory.value = []
  expandedSessions.value = {}
  sessionResults.value = {}
  toastStore.addToast('Вся история поисков удалена', 'success')
}

onMounted(() => {
  loadHistory()
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

.search-history-item {
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

body.light-theme .search-history-item {
  border-color: #e2e8f0;
}

.search-history-header {
  padding: 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: #121212;
}

body.light-theme .search-history-header {
  background: #f0f0f0;
}

.search-history-header:hover {
  background: #1a1a1a;
}

body.light-theme .search-history-header:hover {
  background: #e5e5e5;
}

.search-query {
  font-weight: 600;
  font-size: 14px;
}

.search-meta {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.search-meta-price {
  color: #3b82f6;
}

.btn-delete {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-delete:hover {
  background: #2563eb;
}

.search-results {
  padding: 16px;
  border-top: 1px solid #1f1f1f;
}

body.light-theme .search-results {
  border-top-color: #e2e8f0;
}

.ad-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-results {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
}

.empty-history {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}
</style>