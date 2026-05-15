import time
import threading
import sqlite3
from datetime import datetime, timedelta

import telebot
from telebot.types import LabeledPrice

from config import BOT_TOKEN, SUBSCRIPTION_TYPES, PAYMENT_PROVIDER_TOKEN
from database import (
    init_db, update_user_stats, check_user_subscription, add_user_subscription,
    save_user_temp_data, get_user_temp_data, delete_user_temp_data
)
from parser import AvitoParser
from utils import can_user_monitor, calculate_price_statistics, format_price, find_city_code, validate_price_input, format_ad_message
from keyboards import (
    get_main_menu_keyboard, get_monitoring_time_keyboard, get_monitoring_interval_keyboard,
    get_subscription_keyboard, get_search_results_keyboard, get_back_keyboard,
    get_price_filter_keyboard, get_analysis_keyboard
)
from monitoring import start_monitoring_session
from bot_instance import bot  # Импортируем bot из отдельного файла

# Инициализация базы данных
init_db()

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    subscription = check_user_subscription(message.from_user.id)
    subscription_status = "✅ Активна" if subscription['active'] else "❌ Не активна"
    
    bot.send_message(
        message.chat.id,
        f"👋 Добро пожаловать в *AvitoScannerPro*!\n\n"
        f"💫 Статус подписки: {subscription_status}\n\n"
        "🎯 *Возможности:*\n"
        "• Поиск любых товаров на Avito\n"
        "• Мгновенные уведомления о новых объявлениях\n"
        "• Фильтрация по цене и городу\n"
        "• Анализ рыночных цен (премиум)\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "show_profile")
def show_profile_callback(call):
    """Показать профиль пользователя"""
    profile_command(type('Message', (), {
        'chat': type('Chat', (), {'id': call.message.chat.id}),
        'from_user': call.from_user
    }))

@bot.message_handler(commands=['profile'])
def profile_command(message):
    """Команда профиля"""
    user_id = message.from_user.id
    
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
    stats = cursor.fetchone()
    conn.close()
    
    subscription = check_user_subscription(user_id)
    
    if stats:
        searches_count = stats[1] or 0
        ads_found = stats[2] or 0
        monitoring_sessions = stats[3] or 0
    else:
        searches_count = ads_found = monitoring_sessions = 0
    
    if subscription['active']:
        end_date = subscription['end_date']
        if hasattr(end_date, 'strftime'):
            end_date_str = end_date.strftime("%d.%m.%Y %H:%M")
        else:
            try:
                end_date_obj = datetime.fromisoformat(str(end_date).replace('Z', '+00:00'))
                end_date_str = end_date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                end_date_str = "неизвестно"
        
        subscription_text = f"✅ Активна (до {end_date_str})"
    else:
        subscription_text = "❌ Не активна"
    
    profile_message = (
        f"👤 *Ваш профиль*\n\n"
        f"💫 Подписка: {subscription_text}\n\n"
        f"📊 *Статистика:*\n"
        f"• Поисковых запросов: {searches_count}\n"
        f"• Найдено объявлений: {ads_found}\n"
        f"• Сессий мониторинга: {monitoring_sessions}\n\n"
    )
    
    keyboard = get_main_menu_keyboard()
    
    bot.send_message(
        message.chat.id,
        profile_message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['premium'])
def premium_command(message):
    """Команда премиум"""
    show_subscription_options_callback(type('Call', (), {
        'message': type('Message', (), {'chat': type('Chat', (), {'id': message.chat.id})}),
        'from_user': message.from_user
    }))

@bot.callback_query_handler(func=lambda call: call.data == "show_subscription_options")
def show_subscription_options_callback(call):
    """Показать варианты подписок"""
    subscription = check_user_subscription(call.from_user.id)
    
    if subscription['active']:
        end_date = subscription['end_date']
        if hasattr(end_date, 'strftime'):
            end_date_str = end_date.strftime("%d.%m.%Y %H:%M")
        else:
            try:
                end_date_obj = datetime.fromisoformat(str(end_date).replace('Z', '+00:00'))
                end_date_str = end_date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                end_date_str = "неизвестно"
                
        message_text = (
            f"✅ *У вас активна премиум подписка!*\n\n"
            f"⏰ Действует до: {end_date_str}\n\n"
            f"Теперь вы можете использовать мониторинг объявлений до 8 часов за сессию!"
        )
        
        keyboard = get_main_menu_keyboard()
        
    else:
        message_text = (
            "🌟 *Премиум подписка*\n\n"
            "💡 *Что дает:*\n"
            "• Доступ к мониторингу объявлений\n"
            "• Максимум 8 часов за сессию\n"
            "• Приоритетная обработка запросов\n"
            "• Анализ рыночных цен\n\n"
            "💰 *Выберите вариант подписки:*"
        )
        
        keyboard = get_subscription_keyboard(has_active_subscription=False)
    
    try:
        bot.edit_message_text(
            message_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            bot.send_message(
                call.message.chat.id,
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

@bot.callback_query_handler(func=lambda call: call.data in ["buy_subscription_day", "buy_subscription_month"])
def buy_subscription_callback(call):
    """Обработка покупки подписки"""
    subscription_type = "day" if call.data == "buy_subscription_day" else "month"
    subscription_info = SUBSCRIPTION_TYPES[subscription_type]
    
    prices = [LabeledPrice(label=subscription_info['name'], amount=subscription_info['stars'] * 100)]
    
    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"Премиум подписка - {subscription_info['name']}",
            description=subscription_info['description'],
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="XTR",
            prices=prices,
            payload=f"subscription_{subscription_type}_{call.from_user.id}",
            start_parameter="subscription"
        )
    except Exception as e:
        print(f"Ошибка при создании счета: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при создании счета. Попробуйте позже.")

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_handler(pre_checkout_query):
    """Обработка предварительного запроса оплаты"""
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment_handler(message):
    """Обработка успешной оплаты"""
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    
    if payload.startswith('subscription_'):
        parts = payload.split('_')
        if len(parts) >= 3:
            subscription_type = parts[1]
            target_user_id = int(parts[2])
            
            if subscription_type in SUBSCRIPTION_TYPES:
                days = SUBSCRIPTION_TYPES[subscription_type]['days']
                charge_id = message.successful_payment.telegram_payment_charge_id
                
                add_user_subscription(target_user_id, subscription_type, days, charge_id)
                
                bot.send_message(
                    message.chat.id,
                    f"✅ *Подписка успешно активирована!*\n\n"
                    f"💫 Тип: {SUBSCRIPTION_TYPES[subscription_type]['name']}\n"
                    f"⏰ Срок действия: {days} дней\n\n"
                    f"Теперь вы можете использовать все функции бота!",
                    parse_mode='Markdown'
                )
                
                start_command(message)
                return
    
    bot.send_message(message.chat.id, "❌ Ошибка активации подписки. Обратитесь в поддержку.")

@bot.callback_query_handler(func=lambda call: call.data == "market_analysis")
def market_analysis_callback(call):
    """Обработчик кнопки анализа рынка"""
    if not can_user_monitor(call.from_user.id):
        keyboard = get_subscription_keyboard(has_active_subscription=False)
        
        try:
            bot.edit_message_text(
                "❌ *Доступно только с подпиской!*\n\n"
                "Для использования анализа рынка необходимо приобрести премиум подписку.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                bot.send_message(
                    call.message.chat.id,
                    "❌ *Доступно только с подпиской!*\n\n"
                    "Для использования анализа рынка необходимо приобрести премиум подписку.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
        return
    
    msg = bot.send_message(call.message.chat.id, "🔍 *Введите поисковый запрос для анализа рынка:*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_market_analysis_query)

def process_market_analysis_query(message):
    """Обработка запроса для анализа рынка"""
    search_query = message.text.strip()
    if not search_query:
        msg = bot.send_message(message.chat.id, "❌ Запрос не может быть пустым. Введите поисковый запрос:")
        bot.register_next_step_handler(msg, process_market_analysis_query)
        return
    
    save_user_temp_data(message.from_user.id, {
        'action': 'market_analysis',
        'search_query': search_query
    })
    
    msg = bot.send_message(
        message.chat.id,
        "🏙️ *Введите название города для анализа:*\n\n"
        "Например: *Москва* или *Санкт-Петербург*\n"
        "Или введите *Все регионы* для анализа по всей России",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_market_analysis_city)

def process_market_analysis_city(message):
    """Обработка города для анализа рынка"""
    city_input = message.text.strip()
    
    temp_data = get_user_temp_data(message.from_user.id)
    if not temp_data or temp_data.get('action') != 'market_analysis':
        bot.send_message(message.chat.id, "❌ Сессия устарела. Начните заново.")
        return
    
    search_query = temp_data['search_query']
    city_code, city_name = find_city_code(city_input)
    
    bot.send_message(message.chat.id, "📊 *Анализирую рынок...* Это может занять несколько минут.", parse_mode='Markdown')
    
    threading.Thread(
        target=perform_market_analysis,
        args=(message, search_query, city_code, city_name)
    ).start()

def perform_market_analysis(message, search_query, city_code, city_name):
    """Выполнение анализа рынка"""
    try:
        parser = AvitoParser()
        
        ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            max_items=50,
            user_id=message.from_user.id,
            pages=4
        )
        
        parser.close()
        
        if not ads:
            bot.send_message(message.chat.id, "❌ Не удалось найти объявления для анализа.")
            return
        
        print(f"Для анализа собрано {len(ads)} объявлений")
        
        stats = calculate_price_statistics(ads)
        
        if not stats:
            bot.send_message(message.chat.id, "❌ Не удалось проанализировать цены объявлений.")
            return
        
        report = (
            f"📊 *Анализ рынка:* {search_query}\n"
            f"🏙️ *Регион:* {city_name}\n"
            f"📈 *Проанализировано объявлений:* {len(ads)}\n\n"
            f"💰 *Статистика цен:*\n"
            f"• Медианная цена: {format_price(stats['median'])}\n"
            f"• Средняя цена: {format_price(stats['mean'])}\n"
            f"• Минимальная цена: {format_price(stats['min'])}\n"
            f"• Максимальная цена: {format_price(stats['max'])}\n"
        )
        
        bot.send_message(
            message.chat.id,
            report,
            reply_markup=get_analysis_keyboard(),
            parse_mode='Markdown'
        )
        
        update_user_stats(message.from_user.id, searches_increment=1, ads_increment=len(ads))
        
    except Exception as e:
        error_msg = f"❌ Ошибка при анализе рынка: {str(e)}"
        print(error_msg)
        bot.send_message(message.chat.id, error_msg)

@bot.callback_query_handler(func=lambda call: call.data == "start_monitoring_direct")
def start_monitoring_direct_callback(call):
    """Обработчик кнопки мониторинга"""
    if not can_user_monitor(call.from_user.id):
        keyboard = get_subscription_keyboard(has_active_subscription=False)
        
        try:
            bot.edit_message_text(
                "❌ *Доступно только с подпиской!*\n\n"
                "Для использования мониторинга необходимо приобрести премиум подписку.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                bot.send_message(
                    call.message.chat.id,
                    "❌ *Доступно только с подпиской!*\n\n"
                    "Для использования мониторинга необходимо приобрести премиум подписку.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
        return
    
    msg = bot.send_message(call.message.chat.id, "🔍 *Введите поисковый запрос для мониторинга:*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_monitoring_query)

def process_monitoring_query(message):
    """Обработка запроса для мониторинга"""
    search_query = message.text.strip()
    if not search_query:
        msg = bot.send_message(message.chat.id, "❌ Запрос не может быть пустым. Введите поисковый запрос:")
        bot.register_next_step_handler(msg, process_monitoring_query)
        return
    
    save_user_temp_data(message.from_user.id, {
        'action': 'monitoring',
        'search_query': search_query
    })
    
    msg = bot.send_message(
        message.chat.id,
        "🏙️ *Введите название города для мониторинга:*\n\n"
        "Например: *Москва* или *Санкт-Петербург*\n"
        "Или введите *Все регионы* для поиска по всей России",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_monitoring_city)

def process_monitoring_city(message):
    """Обработка города для мониторинга"""
    city_input = message.text.strip()
    
    temp_data = get_user_temp_data(message.from_user.id)
    if not temp_data or temp_data.get('action') != 'monitoring':
        bot.send_message(message.chat.id, "❌ Сессия устарела. Начните заново.")
        return
    
    search_query = temp_data['search_query']
    city_code, city_name = find_city_code(city_input)
    
    save_user_temp_data(message.from_user.id, {
        'action': 'monitoring',
        'search_query': search_query,
        'city_code': city_code,
        'city_name': city_name
    })
    
    ask_price_range(message)

def ask_price_range(message):
    """Запрос диапазона цен"""
    msg = bot.send_message(
        message.chat.id,
        "💰 *Укажите минимальную цену:*\n\n"
        "Например: 1000\n"
        "Или напишите 'нет' для пропуска",
        reply_markup=get_price_filter_keyboard(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_min_price)

def process_min_price(message):
    """Обработка минимальной цены"""
    if hasattr(message, 'data') and message.data == 'price_none':
        min_price = None
    else:
        min_price = validate_price_input(message.text)
    
    temp_data = get_user_temp_data(message.from_user.id)
    if temp_data:
        temp_data['min_price'] = min_price
        save_user_temp_data(message.from_user.id, temp_data)
    
    ask_max_price(message, min_price)

def ask_max_price(message, min_price):
    """Запрос максимальной цены"""
    price_text = f" (от {min_price} руб.)" if min_price else ""
    
    msg = bot.send_message(
        message.chat.id,
        f"💰 *Укажите максимальную цену{price_text}:*\n\n"
        "Например: 50000\n"
        "Или напишите 'нет' для пропуска",
        reply_markup=get_price_filter_keyboard(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_max_price)

def process_max_price(message):
    """Обработка максимальной цены"""
    if hasattr(message, 'data') and message.data == 'price_none':
        max_price = None
    else:
        max_price = validate_price_input(message.text)
    
    temp_data = get_user_temp_data(message.from_user.id)
    if temp_data:
        temp_data['max_price'] = max_price
        save_user_temp_data(message.from_user.id, temp_data)
    
    ask_monitoring_time(message)

def ask_monitoring_time(message):
    """Запрос времени мониторинга"""
    bot.send_message(
        message.chat.id,
        "⏰ *Выберите время мониторинга:*",
        reply_markup=get_monitoring_time_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("monitoring_time_"))
def handle_monitoring_time_selection(call):
    """Обработка выбора времени мониторинга"""
    monitoring_time = int(call.data.replace("monitoring_time_", ""))
    
    temp_data = get_user_temp_data(call.from_user.id)
    if not temp_data or temp_data.get('action') != 'monitoring':
        bot.send_message(call.message.chat.id, "❌ Сессия устарела. Начните заново.")
        return
    
    temp_data['monitoring_time'] = monitoring_time
    temp_data['monitoring_times'] = {
        '5 минут': 5,
        '15 минут': 15,
        '30 минут': 30,
        '1 час': 60,
        '2 часа': 120,
        '3 часа': 180,
        '4 часа': 240,
        '6 часов': 360,
        '8 часов': 480
    }
    save_user_temp_data(call.from_user.id, temp_data)
    
    ask_monitoring_interval(call.message)

def ask_monitoring_interval(message):
    """Запрос интервала мониторинга"""
    bot.send_message(
        message.chat.id,
        "🔄 *Выберите интервал проверки:*",
        reply_markup=get_monitoring_interval_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("monitoring_interval_"))
def handle_monitoring_interval_selection(call):
    """Обработка выбора интервала мониторинга"""
    interval = int(call.data.replace("monitoring_interval_", ""))
    
    temp_data = get_user_temp_data(call.from_user.id)
    if not temp_data or temp_data.get('action') != 'monitoring':
        bot.send_message(call.message.chat.id, "❌ Сессия устарела. Начните заново.")
        return
    
    search_query = temp_data['search_query']
    city_name = temp_data.get('city_name', 'Все регионы')
    min_price = temp_data.get('min_price')
    max_price = temp_data.get('max_price')
    monitoring_time = temp_data.get('monitoring_time')
    
    price_text = ""
    if min_price and max_price:
        price_text = f"💰 *Цена:* от {min_price} до {max_price} руб.\n"
    elif min_price:
        price_text = f"💰 *Цена:* от {min_price} руб.\n"
    elif max_price:
        price_text = f"💰 *Цена:* до {max_price} руб.\n"
    
    monitoring_time_text = [k for k, v in temp_data['monitoring_times'].items() if v == monitoring_time][0]
    interval_text = [k for k, v in {
        '1 минута': 1,
        '2 минуты': 2,
        '5 минут': 5
    }.items() if v == interval][0]
    
    summary = (
        f"🔍 *Настройки мониторинга:*\n\n"
        f"📋 *Запрос:* {search_query}\n"
        f"🏙️ *Город:* {city_name}\n"
        f"{price_text}"
        f"⏰ *Время мониторинга:* {monitoring_time_text}\n"
        f"🔄 *Интервал проверки:* {interval_text}\n\n"
        f"✅ *Запускаю мониторинг...*"
    )
    
    bot.edit_message_text(
        summary,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='Markdown'
    )
    
    threading.Thread(
        target=start_monitoring_session,
        args=(call, temp_data, interval)
    ).start()

@bot.callback_query_handler(func=lambda call: call.data == "start_search")
def start_search_callback(call):
    """Обработчик кнопки начала поиска"""
    msg = bot.send_message(call.message.chat.id, "🔍 *Введите поисковый запрос:*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_search_query)

def process_search_query(message):
    """Обработка поискового запроса"""
    search_query = message.text.strip()
    if not search_query:
        msg = bot.send_message(message.chat.id, "❌ Запрос не может быть пустым. Введите поисковый запрос:")
        bot.register_next_step_handler(msg, process_search_query)
        return
    
    save_user_temp_data(message.from_user.id, {
        'action': 'search',
        'search_query': search_query
    })
    
    msg = bot.send_message(
        message.chat.id,
        "🏙️ *Введите название города для поиска:*\n\n"
        "Например: *Москва* или *Санкт-Петербург*\n"
        "Или введите *Все регионы* для поиска по всей России",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_search_city)

def process_search_city(message):
    """Обработка города для поиска"""
    city_input = message.text.strip()
    
    temp_data = get_user_temp_data(message.from_user.id)
    if not temp_data or temp_data.get('action') != 'search':
        bot.send_message(message.chat.id, "❌ Сессия устарела. Начните заново.")
        return
    
    search_query = temp_data['search_query']
    city_code, city_name = find_city_code(city_input)
    
    bot.send_message(message.chat.id, "🔍 *Ищу объявления...*", parse_mode='Markdown')
    
    threading.Thread(
        target=perform_search,
        args=(message, search_query, city_code, city_name)
    ).start()

def perform_search(message, search_query, city_code, city_name):
    """Выполнение поиска"""
    try:
        parser = AvitoParser()
        ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            max_items=50,
            user_id=message.from_user.id
        )
        parser.close()
        
        if not ads:
            keyboard = get_search_results_keyboard(message.from_user.id)
            
            bot.send_message(
                message.chat.id,
                f"❌ *По запросу '{search_query}' в городе {city_name} ничего не найдено.*\n\n"
                "Попробуйте:\n"
                "• Изменить поисковый запрос\n"
                "• Выбрать другой город\n"
                "• Убрать фильтры цены",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return
        
        results_message = f"🔍 *Результаты поиска:* {search_query}\n🏙️ *Город:* {city_name}\n📊 *Найдено объявлений:* {len(ads)}\n\n"
        
        for i, ad in enumerate(ads[:5], 1):
            results_message += format_ad_message(ad, i) + "\n"
        
        if len(ads) > 5:
            results_message += f"*... и еще {len(ads) - 5} объявлений*"
        
        bot.send_message(
            message.chat.id,
            results_message,
            reply_markup=get_search_results_keyboard(message.from_user.id),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        update_user_stats(message.from_user.id, searches_increment=1, ads_increment=len(ads))
        
    except Exception as e:
        error_msg = f"❌ Ошибка при поиске: {str(e)}"
        bot.send_message(message.chat.id, error_msg)

def perform_search(message, search_query, city_code, city_name):
    """Выполнение поиска"""
    try:
        parser = AvitoParser()
        ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            max_items=50,
            user_id=message.from_user.id
        )
        parser.close()

        if not ads:
            keyboard = get_search_results_keyboard(message.from_user.id)

            bot.send_message(
                message.chat.id,
                f"❌ *По запросу '{search_query}' в городе {city_name} ничего не найдено.*\n\n"
                "Попробуйте:\n"
                "• Изменить поисковый запрос\n"
                "• Выбрать другой город\n"
                "• Убрать фильтры цены",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return

        bot.send_message(
            message.chat.id,
            f"🔍 *Результаты поиска:* {search_query}\n🏙️ *Город:* {city_name}\n📊 *Найдено объявлений:* {len(ads)}",
            parse_mode='Markdown'
        )

        for i, ad in enumerate(ads, 1):
            bot.send_message(
                message.chat.id,
                format_ad_message(ad, i),
                reply_markup=get_search_results_keyboard(message.from_user.id) if i == len(ads) else None,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

        update_user_stats(message.from_user.id, searches_increment=1, ads_increment=len(ads))

    except Exception as e:
        error_msg = f"❌ Ошибка при поиске: {str(e)}"
        bot.send_message(message.chat.id, error_msg)


@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_callback(call):
    """Возврат в главное меню"""
    start_command(type('Message', (), {
        'chat': type('Chat', (), {'id': call.message.chat.id}),
        'from_user': call.from_user
    }))

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def show_help_callback(call):
    """Показ справки"""
    help_text = (
        "ℹ️ *Помощь по боту AvitoScannerPro*\n\n"
        "🎯 *Основные команды:*\n"
        "• /start - Главное меню\n"
        "• /profile - Ваш профиль\n"
        "• /premium - Премиум подписка\n\n"
        "🔍 *Поиск объявлений:*\n"
        "1. Нажмите 'Начать поиск'\n"
        "2. Введите поисковый запрос\n"
        "3. Введите название города\n"
        "4. Получите результаты\n\n"
        "🔄 *Мониторинг (премиум):*\n"
        "• Автоматическая проверка новых объявлений\n"
        "• Настройка интервала проверки\n"
        "• Уведомления о новых предложениях\n"
        "• Фильтрация по цене\n\n"
        "📊 *Анализ рынка (премиум):*\n"
        "• Статистика цен по запросу\n"
        "• Анализ 200+ объявлений\n"
        "• Медианные и средние цены\n\n"
        "💫 *Премиум подписка:*\n"
        "• Доступ к мониторингу\n"
        "• Доступ к анализу рынка\n"
        "• Приоритетная обработка\n\n"
        "❓ *Частые проблемы:*\n"
        "• Если поиск не работает - попробуйте позже\n"
        "• Для обхода ограничений используйте премиум\n"
        "• При ошибках - перезапустите бот /start"
    )
    
    try:
        bot.edit_message_text(
            help_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard(),
            parse_mode='Markdown'
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            bot.send_message(
                call.message.chat.id,
                help_text,
                reply_markup=get_back_keyboard(),
                parse_mode='Markdown'
            )
