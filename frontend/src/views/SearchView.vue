<template>
  <div class="animate-fade-in">
    <div class="card">
      <div class="card-title">Поиск на Avito</div>
      
      <!-- Режим перекупа iPhone -->
      <div v-if="resellerStore.isActive" class="form-group">
        <label class="form-label">Быстрый выбор модели iPhone</label>
        <div class="iphone-models-grid">
          <div 
            v-for="model in iphoneModels" 
            :key="model.value"
            class="iphone-model-btn"
            :class="{ selected: selectedModel === model.value }"
            @click="selectModel(model)"
          >
            {{ model.name }}
          </div>
        </div>
        
        <div 
          v-if="selectedModel && availableStorage.length > 0 && selectedModel !== 'iPhone'"
          class="storage-grid"
        >
          <div 
            v-for="storage in availableStorage"
            :key="storage"
            class="storage-btn"
            :class="{ selected: selectedStorage === storage }"
            @click="selectStorage(storage)"
          >
            {{ storage }}
          </div>
        </div>
      </div>
      
      <div class="form-group">
        <label class="form-label">Поисковый запрос</label>
        <input 
          type="text" 
          class="form-input" 
          v-model="form.query" 
          placeholder="Например: iPhone 15 Pro Max"
          @keyup.enter="performSearch"
        >
      </div>
      
      <div class="form-group">
        <label class="form-label">Город</label>
        <select class="form-select" v-model="form.city">
          <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
        </select>
      </div>
      
      <div class="grid-2col">
        <div class="form-group">
          <label class="form-label">Минимальная цена (₽)</label>
          <input 
            type="number" 
            class="form-input" 
            v-model="form.minPrice" 
            placeholder="Необязательно"
          >
        </div>
        <div class="form-group">
          <label class="form-label">Максимальная цена (₽)</label>
          <input 
            type="number" 
            class="form-input" 
            v-model="form.maxPrice" 
            placeholder="Необязательно"
          >
        </div>
      </div>
      
      <button class="btn btn-primary" @click="performSearch" :disabled="loading">
        {{ loading ? 'Поиск...' : 'Найти' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useResellerStore } from '@/stores/reseller'
import { useUserStore } from '@/stores/user'
import { useToastStore } from '@/stores/toast'
import { CITIES, IPHONE_MODELS } from '@/utils/constants'
import { useFormatters } from '@/composables/useFormatters'

const resellerStore = useResellerStore()
const userStore = useUserStore()
const toastStore = useToastStore()
const { formatPriceNum } = useFormatters()

const cities = CITIES
const iphoneModels = IPHONE_MODELS

const form = reactive({
  query: '',
  city: 'Все регионы',
  minPrice: '',
  maxPrice: ''
})

const loading = ref(false)
const selectedModel = ref(null)
const selectedStorage = ref(null)
const availableStorage = ref([])

const selectModel = (model) => {
  selectedModel.value = model.value
  availableStorage.value = model.storage || []
  selectedStorage.value = null
  form.query = selectedModel.value
}

const selectStorage = (storage) => {
  selectedStorage.value = storage
  form.query = selectedModel.value + ' ' + storage
}

const performSearch = async () => {
  if (!form.query.trim()) {
    toastStore.addToast('Введите поисковый запрос', 'error')
    return
  }
  
  if (userStore.stats.active_processes >= userStore.maxProcesses) {
    toastStore.addToast(`Достигнут лимит одновременных процессов (${userStore.maxProcesses})`, 'error')
    return
  }
  
  loading.value = true
  
  try {
    const payload = {
      search_query: form.query,
      city: form.city
    }
    if (form.minPrice) payload.min_price = parseInt(form.minPrice)
    if (form.maxPrice) payload.max_price = parseInt(form.maxPrice)
    
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    const data = await response.json()
    
    if (data.success) {
      toastStore.addToast(data.message, 'success')
      await userStore.fetchActiveProcesses()
      await userStore.fetchStats()
    } else {
      toastStore.addToast(data.error || 'Ошибка поиска', 'error')
    }
  } catch (error) {
    toastStore.addToast('Ошибка соединения', 'error')
  } finally {
    loading.value = false
  }
}
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

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #9ca3af;
}

body.light-theme .form-label {
  color: #4a5568;
}

.form-input, .form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  font-size: 14px;
  background: #1a1a1a;
  color: #e2e8f0;
}

body.light-theme .form-input,
body.light-theme .form-select {
  background: white;
  border-color: #e2e8f0;
  color: #1a202c;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
}

.grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  font-family: inherit;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  width: 100%;
  font-weight: 600;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.iphone-models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 8px;
  margin-bottom: 20px;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.iphone-model-btn, .storage-btn {
  border: 1px solid #2a2a2a;
  padding: 8px 4px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 500;
  text-align: center;
  background: #121212;
  color: #e2e8f0;
}

body.light-theme .iphone-model-btn,
body.light-theme .storage-btn {
  background: #f0f0f0;
  border-color: #e2e8f0;
  color: #4a5568;
}

.iphone-model-btn.selected, .storage-btn.selected {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
  font-weight: 600;
}

.storage-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .grid-2col {
    grid-template-columns: 1fr;
  }
  .iphone-models-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>