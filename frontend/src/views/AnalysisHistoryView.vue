<template>
  <div class="animate-fade-in">
    <div class="card">
      <div class="card-title">
        История анализов
        <button class="btn-delete-all" @click="clearAllHistory" v-if="analysisHistory.length > 0">
          Удалить все
        </button>
      </div>
      
      <div class="analysis-history-list" v-if="analysisHistory.length > 0">
        <div 
          v-for="item in analysisHistory" 
          :key="item.session_id"
          class="analysis-history-item"
          :class="{ expanded: expandedSessions[item.session_id] }"
        >
          <!-- Заголовок - всегда виден, при клике раскрывается статистика и кнопка -->
          <div class="analysis-history-header" @click="toggleSession(item.session_id)">
            <div class="analysis-info">
              <div class="analysis-query">{{ item.search_query }}</div>
              <div class="analysis-meta">
                {{ item.city }} • Проанализировано: {{ item.results_count }} • {{ formatDateWithYear(item.created_at) }}
              </div>
            </div>
            <div class="analysis-actions" @click.stop>
              <button class="btn-delete" @click="deleteSession(item.session_id)">Удалить</button>
            </div>
          </div>
          
          <!-- Статистика и кнопка - показываются сразу при разворачивании -->
          <div class="analysis-results" v-if="expandedSessions[item.session_id]">
            <!-- Загрузчик -->
            <div v-if="!analysisResults[item.session_id]" class="loading-results">
              Загрузка статистики...
            </div>
            
            <!-- Статистика цен - всегда видна после загрузки -->
            <template v-else>
              <div class="stats-grid">
                <div class="stat-card">
                  <div class="stat-card-label">Медианная цена</div>
                  <div class="stat-card-value">{{ formatPrice(analysisResults[item.session_id].stats.median) }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-card-label">Средняя цена</div>
                  <div class="stat-card-value">{{ formatPrice(analysisResults[item.session_id].stats.mean) }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-card-label">Минимум</div>
                  <div class="stat-card-value">{{ formatPrice(analysisResults[item.session_id].stats.min) }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-card-label">Максимум</div>
                  <div class="stat-card-value">{{ formatPrice(analysisResults[item.session_id].stats.max) }}</div>
                </div>
              </div>
              
              <!-- Кнопка показа объявлений -->
              <div class="show-all-ads-btn-container">
                <button 
                  class="btn-show-all-ads" 
                  @click="toggleShowAllAds(item.session_id)"
                  :disabled="loadingAds[item.session_id]"
                >
                  <span v-if="!showingAllAds[item.session_id]">Показать все объявления ({{ analysisResults[item.session_id].ads_count }})</span>
                  <span v-else>Скрыть объявления</span>
                </button>
              </div>
              
              <!-- Список объявлений -->
              <div class="ad-list" v-if="showingAllAds[item.session_id]">
                <div v-if="allAdsLoading[item.session_id]" class="loading-results">
                  Загрузка объявлений...
                </div>
                <template v-else>
                  <AdCard 
                    v-for="(ad, idx) in allAdsData[item.session_id]" 
                    :key="ad.ad_id"
                    :ad="ad"
                    :index="idx + 1"
                  />
                  <div v-if="allAdsData[item.session_id] && allAdsData[item.session_id].length === 0" class="empty-ads">
                    Нет объявлений для отображения
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-history">
        История анализов пуста
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
const { formatPrice, formatDateWithYear } = useFormatters()

const analysisHistory = ref([])
const expandedSessions = ref({})
const analysisResults = ref({})
const showingAllAds = ref({})
const allAdsData = ref({})
const allAdsLoading = ref({})
const loadingAds = ref({})

const loadHistory = async () => {
  try {
    const response = await fetch('/api/analysis-history')
    const data = await response.json()
    analysisHistory.value = data.history || []
  } catch (error) {
    console.error('Error loading analysis history:', error)
  }
}

const toggleSession = async (sessionId) => {
  if (expandedSessions.value[sessionId]) {
    expandedSessions.value[sessionId] = false
    showingAllAds.value[sessionId] = false
  } else {
    expandedSessions.value[sessionId] = true
    if (!analysisResults.value[sessionId]) {
      await loadSessionResults(sessionId)
    }
  }
}

const loadSessionResults = async (sessionId) => {
  try {
    const response = await fetch(`/api/analysis-history/${sessionId}/results`)
    const data = await response.json()
    analysisResults.value[sessionId] = data.results
  } catch (error) {
    console.error('Error loading session results:', error)
    analysisResults.value[sessionId] = null
  }
}

const loadAllAds = async (sessionId) => {
  if (allAdsData.value[sessionId]) return
  
  allAdsLoading.value[sessionId] = true
  loadingAds.value[sessionId] = true
  
  try {
    const response = await fetch(`/api/analysis-history/${sessionId}/all-ads`)
    const data = await response.json()
    allAdsData.value[sessionId] = data.ads || []
  } catch (error) {
    console.error('Error loading all ads:', error)
    allAdsData.value[sessionId] = []
    toastStore.addToast('Ошибка загрузки объявлений', 'error')
  } finally {
    allAdsLoading.value[sessionId] = false
    loadingAds.value[sessionId] = false
  }
}

const toggleShowAllAds = async (sessionId) => {
  if (showingAllAds.value[sessionId]) {
    showingAllAds.value[sessionId] = false
  } else {
    showingAllAds.value[sessionId] = true
    await loadAllAds(sessionId)
  }
}

const deleteSession = async (sessionId) => {
  if (!confirm('Удалить эту историю анализа?')) return
  
  try {
    await fetch(`/api/analysis-history/${sessionId}`, { method: 'DELETE' })
    analysisHistory.value = analysisHistory.value.filter(h => h.session_id !== sessionId)
    delete expandedSessions.value[sessionId]
    delete analysisResults.value[sessionId]
    delete showingAllAds.value[sessionId]
    delete allAdsData.value[sessionId]
    toastStore.addToast('История анализа удалена', 'success')
  } catch (error) {
    toastStore.addToast('Ошибка удаления', 'error')
  }
}

const clearAllHistory = async () => {
  if (!confirm('Удалить ВСЮ историю анализов?')) return
  
  for (const item of analysisHistory.value) {
    try {
      await fetch(`/api/analysis-history/${item.session_id}`, { method: 'DELETE' })
    } catch (error) {}
  }
  
  analysisHistory.value = []
  expandedSessions.value = {}
  analysisResults.value = {}
  showingAllAds.value = {}
  allAdsData.value = {}
  toastStore.addToast('Вся история анализов удалена', 'success')
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.card {
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
  border: 1px solid;
  background: inherit;
  border-color: #1a1a1a;
  width: 100%;
  max-width: 100%;
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
  background: #eab308;
  color: #1a1a1a;
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-delete-all:hover {
  background: #ca8a04;
}

.analysis-history-item {
  border: 1px solid;
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  border-color: #1f1f1f;
}

body.light-theme .analysis-history-item {
  border-color: #e2e8f0;
}

.analysis-history-header {
  padding: 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: #121212;
}

body.light-theme .analysis-history-header {
  background: #f0f0f0;
}

.analysis-history-header:hover {
  background: #1a1a1a;
}

body.light-theme .analysis-history-header:hover {
  background: #e5e5e5;
}

.analysis-query {
  font-weight: 600;
  font-size: 14px;
}

.analysis-meta {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.btn-delete {
  background: #eab308;
  color: #1a1a1a;
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-delete:hover {
  background: #ca8a04;
}

.analysis-results {
  padding: 16px;
  border-top: 1px solid;
  border-top-color: #1f1f1f;
}

body.light-theme .analysis-results {
  border-top-color: #e2e8f0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  border: 1px solid;
  background: #111111;
  border-color: #1f1f1f;
}

body.light-theme .stat-card {
  background: #fafafa;
  border-color: #e2e8f0;
}

.stat-card-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 6px;
}

.stat-card-value {
  font-size: 20px;
  font-weight: 700;
  color: #eab308;
}

.show-all-ads-btn-container {
  margin-bottom: 20px;
  text-align: center;
}

.btn-show-all-ads {
  background: #2a2a2a;
  border: none;
  color: #e2e8f0;
  padding: 10px 24px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  width: auto;
  min-width: 200px;
}

.btn-show-all-ads:hover {
  background: #3a3a3a;
}

.btn-show-all-ads:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

body.light-theme .btn-show-all-ads {
  background: #e2e8f0;
  color: #1a202c;
}

body.light-theme .btn-show-all-ads:hover {
  background: #cbd5e1;
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

.empty-ads {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
}

.empty-history {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .btn-show-all-ads {
    width: 100%;
    min-width: unset;
  }
}
</style>