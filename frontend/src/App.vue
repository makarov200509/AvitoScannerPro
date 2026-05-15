<template>
  <div id="app">
    <router-view />
    <ToastNotifications />
  </div>
</template>

<script setup>
import ToastNotifications from '@/components/ToastNotifications.vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
themeStore.initTheme()
</script>