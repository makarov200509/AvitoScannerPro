<template>
  <div v-if="visible" class="modal-overlay" @click="handleClose">
    <div class="modal" @click.stop>
      <div class="modal-title">Сменить пароль</div>
      
      <input 
        type="password" 
        class="modal-input" 
        v-model="form.currentPassword" 
        placeholder="Текущий пароль"
      >
      
      <input 
        type="password" 
        class="modal-input" 
        v-model="form.newPassword" 
        placeholder="Новый пароль"
      >
      
      <input 
        type="password" 
        class="modal-input" 
        v-model="form.confirmPassword" 
        placeholder="Подтвердите пароль"
      >
      
      <div class="modal-buttons">
        <button class="modal-btn modal-btn-secondary" @click="handleClose">Отмена</button>
        <button class="modal-btn modal-btn-primary" @click="changePassword" :disabled="loading">
          {{ loading ? 'Смена...' : 'Сменить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
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

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(false)

const handleClose = () => {
  form.currentPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
  emit('update:visible', false)
}

const changePassword = async () => {
  if (!form.currentPassword || !form.newPassword) {
    toastStore.addToast('Заполните все поля', 'error')
    return
  }
  
  if (form.newPassword.length < 4) {
    toastStore.addToast('Новый пароль должен содержать минимум 4 символа', 'error')
    return
  }
  
  if (form.newPassword !== form.confirmPassword) {
    toastStore.addToast('Пароли не совпадают', 'error')
    return
  }
  
  loading.value = true
  
  try {
    const response = await fetch('/api/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_password: form.currentPassword,
        new_password: form.newPassword
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      toastStore.addToast('Пароль изменен', 'success')
      handleClose()
      emit('success')
    } else {
      toastStore.addToast(data.error || 'Ошибка смены пароля', 'error')
    }
  } catch (error) {
    toastStore.addToast('Ошибка соединения', 'error')
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
  border-radius: 12px;
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
  margin-bottom: 20px;
}

.modal-input {
  width: 100%;
  padding: 10px 14px;
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 6px;
  color: #e2e8f0;
  margin-bottom: 16px;
}

body.light-theme .modal-input {
  background: white;
  border-color: #e2e8f0;
  color: #1a202c;
}

.modal-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.modal-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
}

.modal-btn-primary {
  background: #3b82f6;
  color: white;
  font-weight: 600;
}

.modal-btn-primary:hover {
  background: #2563eb;
}

.modal-btn-primary:disabled {
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