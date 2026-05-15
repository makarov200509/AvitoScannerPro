<template>
  <div class="header animate-fade-in">
    <div class="logo" @click.stop="toggleAvatarMenu">
      <img 
        :src="avatarUrl" 
        alt="Avatar" 
        class="logo-avatar" 
        @error="useDefaultAvatar"
      >
      <div>
        <h1>AvitoScannerPro</h1>
        <p>Поиск и мониторинг Avito</p>
      </div>
    </div>
    
    <div class="avatar-menu" :class="{ show: avatarMenuVisible }" @click.stop>
      <div class="avatar-menu-item" @click="showChangePassword">Сменить пароль</div>
      <div class="avatar-menu-item" @click="toggleStatsOnly">Статистика</div>
      <div class="avatar-menu-item" @click="showHelp">Инструкция</div>
      <div class="avatar-menu-item danger" @click="handleLogout">Выйти</div>
      <div class="avatar-menu-item danger" @click="showDeleteAccount">Удалить аккаунт</div>
    </div>
    
    <div class="header-controls">
      <button class="help-btn" @click="showHelp">Инструкция</button>
      <button 
        class="reseller-mode" 
        :class="{ active: resellerStore.isActive }" 
        @click="resellerStore.toggle"
      >
        Режим перекупа iPhone
      </button>
      <button class="theme-toggle" @click="themeStore.cycleTheme">
        {{ themeStore.themeButtonText() }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useResellerStore } from '@/stores/reseller'
import { useDisplayStore } from '@/stores/display'
import avatarImage from '@/assets/avatar.jpg'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const resellerStore = useResellerStore()
const displayStore = useDisplayStore()

const avatarMenuVisible = ref(false)
const avatarUrl = ref(avatarImage)

const emit = defineEmits(['showChangePassword', 'showDeleteAccount', 'showHelp'])

const toggleAvatarMenu = () => {
  avatarMenuVisible.value = !avatarMenuVisible.value
}

const handleClickOutside = (event) => {
  const logo = document.querySelector('.logo')
  const menu = document.querySelector('.avatar-menu')
  if (avatarMenuVisible.value && logo && menu) {
    if (!logo.contains(event.target) && !menu.contains(event.target)) {
      avatarMenuVisible.value = false
    }
  }
}

const toggleStatsOnly = () => {
  displayStore.toggleStatsVisible()
  avatarMenuVisible.value = false
}

const showChangePassword = () => {
  avatarMenuVisible.value = false
  emit('showChangePassword')
}

const showDeleteAccount = () => {
  avatarMenuVisible.value = false
  emit('showDeleteAccount')
}

const showHelp = () => {
  avatarMenuVisible.value = false
  emit('showHelp')
}

const handleLogout = async () => {
  avatarMenuVisible.value = false
  await authStore.logout()
}

const useDefaultAvatar = (e) => {
  e.target.src = avatarImage
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.header {
  border: 1px solid #1a1a1a;
  border-radius: 12px;
  padding: 20px 28px;
  margin-bottom: 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  background: #0d0d0d;
  position: relative;
}

body.light-theme .header {
  border-color: #e2e8f0;
  background: white;
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
}

.logo-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #3b82f6;
  cursor: pointer;
}

.logo-avatar:hover {
  border-color: #2563eb;
}

.logo h1 {
  font-size: 22px;
  font-weight: 600;
  color: #3b82f6;
}

.logo p {
  font-size: 13px;
  margin-top: 4px;
  color: #9ca3af;
}

body.light-theme .logo p {
  color: #4a5568;
}

.avatar-menu {
  position: absolute;
  top: 70px;
  left: 28px;
  background: #0d0d0d;
  border: 1px solid #1a1a1a;
  border-radius: 12px;
  min-width: 220px;
  z-index: 1000;
  overflow: hidden;
  display: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.avatar-menu.show {
  display: block;
}

body.light-theme .avatar-menu {
  background: white;
  border-color: #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.avatar-menu-item {
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 1px solid #1a1a1a;
}

body.light-theme .avatar-menu-item {
  border-bottom-color: #e2e8f0;
}

.avatar-menu-item:last-child {
  border-bottom: none;
}

.avatar-menu-item:hover {
  background: #1a1a1a;
}

body.light-theme .avatar-menu-item:hover {
  background: #f0f0f0;
}

.avatar-menu-item.danger {
  color: #f87171;
}

.header-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.help-btn,
.reseller-mode,
.theme-toggle {
  border: 1px solid #2a2a2a;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  background: #121212;
  color: #e2e8f0;
}

body.light-theme .help-btn,
body.light-theme .reseller-mode,
body.light-theme .theme-toggle {
  background: #f0f0f0;
  border-color: #e2e8f0;
  color: #4a5568;
}

.help-btn:hover,
.reseller-mode:hover,
.theme-toggle:hover {
  background: #1a1a1a;
}

body.light-theme .help-btn:hover,
body.light-theme .reseller-mode:hover,
body.light-theme .theme-toggle:hover {
  background: #e5e5e5;
}

.reseller-mode.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

body.light-theme .reseller-mode.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

/* Мобильная адаптация */
@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
    margin-bottom: 16px;
    gap: 12px;
  }
  
  .logo {
    gap: 12px;
  }
  
  .logo-avatar {
    width: 40px;
    height: 40px;
  }
  
  .logo h1 {
    font-size: 16px;
  }
  
  .logo p {
    font-size: 10px;
    margin-top: 2px;
  }
  
  .avatar-menu {
    top: 56px;
    left: 16px;
    min-width: 200px;
  }
  
  .avatar-menu-item {
    padding: 10px 14px;
    font-size: 13px;
  }
  
  .header-controls {
    gap: 8px;
  }
  
  .help-btn,
  .reseller-mode,
  .theme-toggle {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>