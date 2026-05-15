<template>
  <div class="ad-item">
    <div class="ad-title">{{ index ? index + '. ' : '' }}{{ ad.title }}</div>
    <div class="ad-price">{{ ad.price }}</div>
    <div class="ad-meta">
      <span>{{ ad.location }}</span>
      <span>{{ ad.date }}</span>
      <a :href="ad.link" target="_blank" class="ad-link" rel="noopener noreferrer">Открыть на Avito</a>
    </div>
  </div>
</template>

<script setup>
defineProps({
  ad: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: null
  }
})
</script>

<style scoped>
.ad-item {
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  padding: 16px;
  position: relative;
}

body.light-theme .ad-item {
  border-color: #e2e8f0;
}

.ad-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  padding-right: 80px;
}

.ad-price {
  font-size: 18px;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 8px;
}

.ad-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #9ca3af;
  flex-wrap: wrap;
}

.ad-link {
  color: #3b82f6;
  text-decoration: none;
}

.ad-link:hover {
  text-decoration: underline;
}
</style>