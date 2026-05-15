<template>
  <div class="qr-section" :class="{ closed: !displayStore.qrVisible }">
    <div class="qr-container">
      <div class="qr-code-wrapper">
        <div id="qrcode" ref="qrcodeContainer"></div>
      </div>
    </div>
    <div class="qr-text">Сканируйте QR-код для перехода в Telegram-бот</div>
    <div class="qr-bot-link">@AvitoScannerProBot</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useDisplayStore } from '@/stores/display'
import QRCodeStyling from 'qr-code-styling'

const displayStore = useDisplayStore()
const qrcodeContainer = ref(null)
let qrCodeInstance = null

const generateQRCode = async () => {
  await nextTick()
  
  if (!qrcodeContainer.value) {
    console.error('Container not found')
    return
  }
  
  // Очищаем контейнер
  qrcodeContainer.value.innerHTML = ''
  
  // Создаём QR-код
  qrCodeInstance = new QRCodeStyling({
    width: 180,
    height: 180,
    type: 'canvas',
    data: 'https://t.me/AvitoScannerProBot',
    image: '',
    dotsOptions: {
      color: '#000000',
      type: 'rounded'
    },
    backgroundOptions: {
      color: '#ffffff'
    },
    cornersSquareOptions: {
      color: '#000000',
      type: 'extra-rounded'
    },
    cornersDotOptions: {
      color: '#000000',
      type: 'dot'
    }
  })
  
  qrCodeInstance.append(qrcodeContainer.value)
}

watch(() => displayStore.qrVisible, async (visible) => {
  if (visible) {
    setTimeout(() => {
      generateQRCode()
    }, 100)
  }
})

onMounted(() => {
  if (displayStore.qrVisible) {
    setTimeout(() => {
      generateQRCode()
    }, 200)
  }
})
</script>

<style scoped>
.qr-section {
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  border: 1px solid;
  margin-bottom: 24px;
  transition: all 0.3s ease;
  background: inherit;
  border-color: #1a1a1a;
}

body.light-theme .qr-section {
  border-color: #e2e8f0;
  background: white;
}

.qr-section.closed {
  display: none;
}

.qr-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto 12px;
}

.qr-code-wrapper {
  display: inline-block;
  background: #ffffff;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.qr-code-wrapper canvas {
  display: block;
  margin: 0 auto;
  border-radius: 8px;
}

body.light-theme .qr-code-wrapper {
  background: #ffffff;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.qr-text {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 12px;
}

.qr-bot-link {
  font-size: 14px;
  font-weight: 500;
  color: #eab308;
  margin-top: 8px;
  font-family: monospace;
}

body.light-theme .qr-text {
  color: #4a5568;
}
</style>