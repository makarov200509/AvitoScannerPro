<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo">
        <h1>AvitoScannerPro</h1>
      </div>

      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Имя пользователя</label>
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
          <label class="form-label">Пароль</label>
          <input 
            type="password" 
            class="form-input" 
            v-model="form.password" 
            placeholder="Введите пароль"
            required
            autocomplete="current-password"
          >
        </div>

        <button type="submit" class="btn" :disabled="authStore.loading">
          {{ authStore.loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <div class="links">
        <router-link to="/register">Нет аккаунта? Зарегистрироваться</router-link>
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
  password: ''
})

const errorMessage = ref('')
const successMessage = ref('')

const handleLogin = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  
  const result = await authStore.login(form.username, form.password)
  
  if (result.success) {
    successMessage.value = 'Вход выполнен успешно!'
    setTimeout(() => {
      router.push('/')
    }, 1000)
  } else {
    errorMessage.value = result.error
  }
}
</script>

<style scoped>
.login-page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a0a 100%);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.login-container {
  background: #0d0d0d;
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 25px 50px -12px rgba(234, 179, 8, 0.15);
  border: 1px solid #2a2a1a;
}

.logo {
  text-align: center;
  margin-bottom: 32px;
}

.logo h1 {
  font-size: 28px;
  font-weight: 600;
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
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

.form-input {
  width: 100%;
  padding: 12px 16px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  font-size: 14px;
  color: #e2e8f0;
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #eab308;
  box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.2);
}

.form-input::placeholder {
  color: #6b7280;
}

.btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  color: #1a1a1a;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:hover {
  background: linear-gradient(135deg, #ca8a04 0%, #b45309 100%);
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.links {
  text-align: center;
  margin-top: 24px;
}

.links a {
  color: #eab308;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s ease;
}

.links a:hover {
  color: #ca8a04;
  text-decoration: underline;
}

.error-message {
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid #dc2626;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 20px;
  color: #f87171;
  font-size: 14px;
  text-align: center;
}

.success-message {
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid #eab308;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 20px;
  color: #eab308;
  font-size: 14px;
  text-align: center;
}
</style>