<template>
  <div v-if="visible" class="modal-overlay" @click="handleClose">
    <div class="modal" @click.stop>
      <div class="modal-title">Удалить аккаунт</div>
      <p class="modal-message">
        Вы уверены? Все данные будут удалены без возможности восстановления.
      </p>
      <div class="modal-buttons">
        <button class="modal-btn modal-btn-secondary" @click="handleClose">Отмена</button>
        <button class="modal-btn modal-btn-danger" @click="deleteAccount" :disabled="loading">
          {{ loading ? 'Удаление...' : 'Удалить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToastStore } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'success'])

const toastStore = useToastStore()
const authStore = useAuthStore()

const loading = ref(false)

const handleClose = () => {
  emit('update:visible', false)
}

const deleteAccount = async () => {
  loading.value = true
  
  try {
    const response = await fetch('/api/delete-account', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    const data = await response.json()
    
    if (data.success) {
      toastStore.addToast('Аккаунт удален', 'success')
      handleClose()
      await authStore.logout()
      emit('success')
    } else {
      toastStore.addToast(data.error || 'Ошибка удаления', 'error')
      handleClose()
    }
  } catch (error) {
    toastStore.addToast('Ошибка соединения', 'error')
    handleClose()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  background: #0d0d0d;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
  border: 1px solid #1a1a1a;
}

body.light-theme .modal {
  background: white;
  border-color: #e2e8f0;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.modal-message {
  font-size: 14px;
  margin-bottom: 20px;
  color: #9ca3af;
}

body.light-theme .modal-message {
  color: #4a5568;
}

.modal-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  border: none;
}

.modal-btn-danger {
  background: #dc2626;
  color: white;
  font-weight: 600;
}

.modal-btn-danger:hover {
  background: #b91c1c;
}

.modal-btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-btn-secondary {
  background: #1a1a1a;
  color: #e2e8f0;
}

body.light-theme .modal-btn-secondary {
  background: #e2e8f0;
  color: #2d3748;
}

.modal-btn-secondary:hover {
  background: #2a2a2a;
}

body.light-theme .modal-btn-secondary:hover {
  background: #cbd5e1;
}
</style>