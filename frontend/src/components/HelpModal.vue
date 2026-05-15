<template>
  <div v-if="visible" class="modal-overlay" @click="handleClose">
    <div class="modal help-modal" @click.stop>
      <div class="modal-header">
        <div class="modal-title">Инструкция по использованию</div>
        <button class="modal-close" @click="handleClose">&times;</button>
      </div>
      
      <div class="modal-body">
        <div class="help-section">
          <div class="help-section-title">Поиск объявлений</div>
          <div class="help-section-content">
            <p>1. Введите поисковый запрос </p>
            <p>2. Выберите город из списка (по умолчанию - "Все регионы")</p>
            <p>3. При желании укажите минимальную и максимальную цену</p>
            <p>4. Нажмите кнопку "Найти"</p>
            <p class="help-note">Результаты появятся в разделе "История поисков"</p>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Мониторинг (отслеживание новых объявлений)</div>
          <div class="help-section-content">
            <p>1. Введите поисковый запрос</p>
            <p>2. Выберите город</p>
            <p>3. Укажите ценовой диапазон (опционально)</p>
            <p>4. Выберите время мониторинга: от 5 минут до 8 часов</p>
            <p>5. Выберите интервал проверки: 1, 2 или 5 минут</p>
            <p>6. Нажмите "Запустить мониторинг"</p>
            <p class="help-note">При появлении новых объявлений вы увидите уведомления над вкладкой "Уведомления"</p>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Анализ рынка</div>
          <div class="help-section-content">
            <p>1. Введите поисковый запрос</p>
            <p>2. Выберите город</p>
            <p>3. Нажмите "Провести анализ"</p>
            <p class="help-note">Анализ собирает до 400 объявлений и показывает:</p>
            <ul>
              <li>Медианную цену</li>
              <li>Среднюю цену</li>
              <li>Максимальную цену</li>
              <li>Минимальную цену</li>
            </ul>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Режим "Перекуп iPhone"</div>
          <div class="help-section-content">
            <p>Специальный режим для тех, кто профессионально занимается скупкой и перепродажей техники Apple.</p>
            <p>Быстрый выбор любой модели iPhone от 3G до 17 Pro Max</p>
            <p class="help-note">Режим помогает быстро находить актуальные предложения по конкретным моделям iPhone без ручного ввода запроса. Рекомендуется пользователям, которые регулярно отслеживают цены на Apple-устройства.</p>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Telegram бот</div>
          <div class="help-section-content">
            <p>Отсканируйте QR-код для перехода в Telegram-бота:</p>
            <p class="help-link">@AvitoScannerProBot</p>
            <p class="help-note">В Telegram-боте доступны те же функции + уведомления о новых объявлениях (может временно не работать в вашей стране)</p>
          </div>
        </div>


        <div class="help-section">
          <div class="help-section-title">Статистика</div>
          <div class="help-section-content">
            <p>Количество выполненных поисковых запросов</p>
            <p>Всего найдено объявлений (за всё время)</p>
            <p>Активные процессы / максимальное количество (7)</p>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="modal-btn modal-btn-primary" @click="handleClose">Понятно</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const handleClose = () => {
  emit('update:visible', false)
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.help-modal {
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: #0d0d0d;
  border-radius: 20px;
  border: 1px solid #1a1a1a;
}

body.light-theme .help-modal {
  background: white;
  border-color: #e2e8f0;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #1a1a1a;
}

body.light-theme .modal-header {
  border-bottom-color: #e2e8f0;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #9ca3af;
  line-height: 1;
}

.modal-close:hover {
  color: #eab308;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #1a1a1a;
  display: flex;
  justify-content: flex-end;
}

body.light-theme .modal-footer {
  border-top-color: #e2e8f0;
}

.help-section {
  margin-bottom: 24px;
}

.help-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #eab308;
  margin-bottom: 12px;
}

.help-section-content {
  padding-left: 12px;
}

.help-section-content p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.5;
}

.help-section-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.help-section-content li {
  margin: 4px 0;
  font-size: 14px;
}

.help-note {
  color: #9ca3af;
  font-size: 12px !important;
  margin-top: 8px !important;
  padding-top: 4px;
  border-top: 1px dashed #1a1a1a;
}

body.light-theme .help-note {
  border-top-color: #e2e8f0;
  color: #6b7280;
}

.help-link {
  color: #eab308;
  font-family: monospace;
  font-size: 14px;
  font-weight: 600;
}

.modal-btn {
  padding: 10px 24px;
  border-radius: 10px;
  cursor: pointer;
  border: none;
  font-size: 14px;
  font-weight: 600;
}

.modal-btn-primary {
  background: #eab308;
  color: #1a1a1a;
}

.modal-btn-primary:hover {
  background: #ca8a04;
}
</style>