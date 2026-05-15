<template>
  <TransitionGroup name="toast" tag="div" class="toast-container">
    <div 
      v-for="toast in toastStore.notifications" 
      :key="toast.id"
      class="notification"
      :class="'notification-' + toast.type"
    >
      <div v-html="toast.message"></div>
    </div>
  </TransitionGroup>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification {
  border-left: 3px solid #eab308;
  padding: 14px 18px;
  border-radius: 10px;
  max-width: 360px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  font-size: 13px;
  background: #0d0d0d;
  color: #e2e8f0;
}

body.light-theme .notification {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: white;
  color: #2d3748;
}

.notification-error {
  border-left-color: #e53e3e;
}

.notification-success {
  border-left-color: #eab308;
}

.notification-info {
  border-left-color: #3b82f6;
}

/* Анимации */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>