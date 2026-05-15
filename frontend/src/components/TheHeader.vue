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
      <div class="avatar-menu-item" @click="toggleQrOnly">QR-код бота</div>
      <div class="avatar-menu-item" @click="showHelp">Инструкция</div>  <!-- НОВЫЙ ПУНКТ -->
      <div class="avatar-menu-item danger" @click="handleLogout">Выйти</div>
      <div class="avatar-menu-item danger" @click="showDeleteAccount">Удалить аккаунт</div>
    </div>
    
    <div class="header-controls">
      <HelpButton @click="showHelp" />  <!-- НОВАЯ КНОПКА ПОМОЩИ -->
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
import HelpButton from './HelpButton.vue'
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

const toggleQrOnly = () => {
  displayStore.toggleQrVisible()
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
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  border: 1px solid;
  transition: all 0.3s ease;
  position: relative;
  background: inherit;
  border-color: #1a1a1a;
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
  position: relative;
}

.logo-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #eab308;
  transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
  cursor: pointer;
}

.logo-avatar:hover {
  transform: scale(1.08);
  border-color: #ca8a04;
  box-shadow: 0 4px 12px rgba(234, 179, 8, 0.3);
}

.logo h1 {
  font-size: 22px;
  font-weight: 600;
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
  left: 0;
  background: #0d0d0d;
  border: 1px solid #1a1a1a;
  border-radius: 12px;
  min-width: 220px;
  z-index: 1000;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: none;
}

.avatar-menu.show {
  display: block;
}

body.light-theme .avatar-menu {
  background: white;
  border-color: #e2e8f0;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

.avatar-menu-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s ease;
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

.reseller-mode, .theme-toggle {
  border: 1px solid;
  padding: 8px 16px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  background: #121212;
  border-color: #1f1f1f;
  color: #e2e8f0;
}

body.light-theme .reseller-mode,
body.light-theme .theme-toggle {
  background: #f0f0f0;
  border-color: #e2e8f0;
  color: #4a5568;
}

.reseller-mode:hover, .theme-toggle:hover {
  background: #1a1a1a;
}

body.light-theme .reseller-mode:hover,
body.light-theme .theme-toggle:hover {
  background: #e5e5e5;
}

.reseller-mode.active {
  background: #eab308 !important;
  border-color: #eab308 !important;
  color: #1a1a1a !important;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    text-align: center;
  }
  .header-controls {
    justify-content: center;
  }
  .avatar-menu {
    left: 50%;
    transform: translateX(-50%);
    top: 80px;
  }
}
</style>