<template>
  <div class="register-page">
    <div class="register-container">
      <div class="logo">
        <h1>AvitoScannerPro</h1>
      </div>

      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label">Имя пользователя (минимум 3 символа)</label>
          <input 
            type="text" 
            class="form-input" 
            v-model="form.username" 
            placeholder="Введите имя пользователя"
            required
            autocomplete="username"
          >
        </div>

        <div class="form-group">
          <label class="form-label">Пароль (минимум 10 символов)</label>
          <input 
            type="password" 
            class="form-input" 
            v-model="form.password" 
            placeholder="Введите пароль"
            required
            autocomplete="new-password"
          >
        </div>

        <div class="form-group">
          <label class="form-label">Подтверждение пароля</label>
          <input 
            type="password" 
            class="form-input" 
            v-model="form.confirmPassword" 
            placeholder="Повторите пароль"
            required
            autocomplete="new-password"
          >
        </div>

        <button type="submit" class="btn" :disabled="authStore.loading">
          {{ authStore.loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <div class="links">
        <router-link to="/login">Уже есть аккаунт? Войти</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const errorMessage = ref('')
const successMessage = ref('')

const handleRegister = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  
  if (!form.username.trim()) {
    errorMessage.value = 'Введите имя пользователя'
    return
  }
  
  if (form.username.length < 3) {
    errorMessage.value = 'Имя пользователя должно содержать минимум 3 символа'
    return
  }
  
  if (!form.password) {
    errorMessage.value = 'Введите пароль'
    return
  }
  
  if (form.password.length < 10) {
      errorMessage.value = 'Пароль должен содержать минимум 10 символов'
      return
  }
  
  if (form.password !== form.confirmPassword) {
    errorMessage.value = 'Пароли не совпадают'
    return
  }
  
  const result = await authStore.register(form.username, form.password)
  
  if (result.success) {
    successMessage.value = 'Регистрация успешна! Перенаправление на страницу входа...'
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } else {
    errorMessage.value = result.error
  }
}
</script>

<style scoped>
.register-page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #404040;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

body.light-theme .register-page {
  background: #3b82f6;
}

.register-container {
  background: #0d0d0d;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  border: 1px solid #1a1a1a;
}

body.light-theme .register-container {
  background: white;
  border-color: #e2e8f0;
}

.logo {
  text-align: center;
  margin-bottom: 32px;
}

.logo h1 {
  font-size: 28px;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 8px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #9ca3af;
}

body.light-theme .form-label {
  color: #4a5568;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  font-size: 14px;
  color: #e2e8f0;
}

body.light-theme .form-input {
  background: white;
  border-color: #e2e8f0;
  color: #1a202c;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-input::placeholder {
  color: #6b7280;
}

.btn {
  width: 100%;
  padding: 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.btn:hover {
  background: #2563eb;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.links {
  text-align: center;
  margin-top: 24px;
}

.links a {
  color: #3b82f6;
  text-decoration: none;
  font-size: 14px;
}

.links a:hover {
  text-decoration: underline;
}

.error-message {
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid #dc2626;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 20px;
  color: #f87171;
  font-size: 14px;
  text-align: center;
}

.success-message {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid #3b82f6;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 20px;
  color: #3b82f6;
  font-size: 14px;
  text-align: center;
}
</style>