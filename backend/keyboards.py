from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import MONITORING_TIMES, MONITORING_INTERVALS

def get_main_menu_keyboard():
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔍 Начать поиск", callback_data="start_search"))
    keyboard.add(InlineKeyboardButton("🔄 Мониторинг", callback_data="start_monitoring_direct"))
    keyboard.add(InlineKeyboardButton("📊 Анализ рынка", callback_data="market_analysis"))
    keyboard.add(InlineKeyboardButton("💫 Премиум", callback_data="show_subscription_options"))
    keyboard.add(InlineKeyboardButton("👤 Профиль", callback_data="show_profile"))
    keyboard.add(InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help"))
    return keyboard

def get_monitoring_time_keyboard():
    """Клавиатура выбора времени мониторинга"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    for time_text in MONITORING_TIMES.keys():
        keyboard.add(InlineKeyboardButton(time_text, callback_data=f"monitoring_time_{MONITORING_TIMES[time_text]}"))
    return keyboard

def get_monitoring_interval_keyboard():
    """Клавиатура выбора интервала мониторинга"""
    keyboard = InlineKeyboardMarkup()
    for interval_text in MONITORING_INTERVALS.keys():
        keyboard.add(InlineKeyboardButton(interval_text, callback_data=f"monitoring_interval_{MONITORING_INTERVALS[interval_text]}"))
    return keyboard

def get_subscription_keyboard(has_active_subscription=False):
    """Клавиатура подписок"""
    keyboard = InlineKeyboardMarkup()
    if not has_active_subscription:
        keyboard.add(InlineKeyboardButton("💫 1 день - 1 звезда", callback_data="buy_subscription_day"))
        keyboard.add(InlineKeyboardButton("💫 1 месяц - 2 звезды", callback_data="buy_subscription_month"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    return keyboard

def get_search_results_keyboard(user_id):
    """Клавиатура для результатов поиска"""
    from utils import can_user_monitor
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Новый поиск", callback_data="start_search"))
    
    if can_user_monitor(user_id):
        keyboard.add(InlineKeyboardButton("🔄 Запустить мониторинг", callback_data="start_monitoring_direct"))
    else:
        keyboard.add(InlineKeyboardButton("💫 Премиум для мониторинга", callback_data="show_subscription_options"))
    
    keyboard.add(InlineKeyboardButton("📊 Профиль", callback_data="show_profile"))
    return keyboard

def get_back_keyboard():
    """Кнопка возврата в главное меню"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    return keyboard

def get_price_filter_keyboard():
    """Клавиатура для фильтра цены"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Без фильтра цены", callback_data="price_none"))
    return keyboard

def get_analysis_keyboard():
    """Клавиатура для анализа рынка"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Новый анализ", callback_data="market_analysis"))
    keyboard.add(InlineKeyboardButton("🔍 Начать поиск", callback_data="start_search"))
    keyboard.add(InlineKeyboardButton("📊 Профиль", callback_data="show_profile"))
    return keyboard