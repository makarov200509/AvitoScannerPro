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
            <p>1. Введите поисковый запрос (например, "iPhone 15 Pro")</p>
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
            <p>4. Выберите <strong>время мониторинга</strong>: от 5 минут до 8 часов</p>
            <p>5. Выберите <strong>интервал проверки</strong>: 1, 2 или 5 минут</p>
            <p>6. Нажмите "Запустить мониторинг"</p>
            <p class="help-note">При появлении новых объявлений вы увидите уведомления в одноимённой вкладке</p>
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
              <li>Минимальную цену</li>
              <li>Максимальную цену</li>
            </ul>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Режим "Перекуп iPhone"</div>
          <div class="help-section-content">
            <p>Специальный режим для быстрого поиска и анализа iPhone:</p>
            <ul>
              <li>Выберите любую модель от iPhone 3G до 17 Pro Max</li>
              <li>При необходимости укажите объём памяти</li>
              <li>Запрос сформируется автоматически</li>
            </ul>
            <p class="help-note">Включите режим кнопкой справа вверху — появится сетка всех моделей</p>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">История поисков и анализов</div>
          <div class="help-section-content">
            <p>Все выполненные поиски и анализы сохраняются в соответствующих вкладках:</p>
            <ul>
              <li><strong>История поисков</strong> — результаты обычного поиска</li>
              <li><strong>История анализов</strong> — результаты анализа рынка</li>
            </ul>
            <p>Любую запись можно развернуть, посмотреть объявления или удалить</p>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Статистика использования</div>
          <div class="help-section-content">
            <p>В блоке статистики отображается:</p>
            <ul>
              <li>Количество выполненных поисковых запросов</li>
              <li>Всего найдено объявлений (за всё время)</li>
              <li>Активные процессы / максимальное количество (7)</li>
            </ul>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Управление аккаунтом</div>
          <div class="help-section-content">
            <p>Нажмите на аватар в левом верхнем углу:</p>
            <ul>
              <li><strong>Сменить пароль</strong> — изменить пароль от аккаунта</li>
              <li><strong>Статистика</strong> — показать/скрыть блок статистики</li>
              <li><strong>Инструкция</strong> — открыть это окно</li>
              <li><strong>Выйти</strong> — завершить сессию</li>
              <li><strong>Удалить аккаунт</strong> — безвозвратное удаление всех данных</li>
            </ul>
          </div>
        </div>

        <div class="help-section">
          <div class="help-section-title">Темы оформления</div>
          <div class="help-section-content">
            <p>Кнопка в правом верхнем углу переключает тёмную и светлую тему</p>
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
  background: rgba(0, 0, 0, 0.7);
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
  border-radius: 12px;
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
  color: #3b82f6;
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
  color: #3b82f6;
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

.modal-btn {
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  font-size: 14px;
  font-weight: 600;
}

.modal-btn-primary {
  background: #3b82f6;
  color: white;
}

.modal-btn-primary:hover {
  background: #2563eb;
}
</style>