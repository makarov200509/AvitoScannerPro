import time
import traceback
from bot_instance import bot
from database import init_db

def main():
    """Главная функция запуска бота"""
    print("Инициализация базы данных...")
    try:
        init_db()
        print("База данных инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
    
    print("Запуск бота...")
    
    # Явно импортируем обработчики
    try:
        import bot_handlers
        print("Обработчики команд загружены")
    except Exception as e:
        print(f"Ошибка при загрузке обработчиков: {e}")
        traceback.print_exc()
        return
    
    # Бесконечный цикл с переподключением
    while True:
        try:
            print("Бот запущен. Ожидание сообщений...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Ошибка в polling: {e}")
            traceback.print_exc()
            print("Переподключение через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    main()