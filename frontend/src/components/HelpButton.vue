<template>
  <button class="theme-toggle" @click="$emit('click')">
    Инструкция
  </button>
</template>

<script setup>
defineEmits(['click'])
</script>

<style scoped>
.theme-toggle {
  border: 1px solid;
  padding: 8px 16px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  background: #121212;
  border-color: #1f1f1f;
  color: #e2e8f0;
  will-change: auto;
}

body.light-theme .theme-toggle {
  background: #f0f0f0;
  border-color: #e2e8f0;
  color: #4a5568;
}

.theme-toggle:hover {
  background: #1a1a1a;
}

body.light-theme .theme-toggle:hover {
  background: #e5e5e5;
}
</style>