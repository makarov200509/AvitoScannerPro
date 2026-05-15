import time
import threading
from datetime import datetime, timedelta
from parser import AvitoParser
from database import add_seen_ad, is_ad_seen, update_user_stats
from utils import format_ad_message
import json
import requests

# URL для отправки уведомлений (через Flask)
WEBHOOK_URL = None

def set_webhook_url(url):
    global WEBHOOK_URL
    WEBHOOK_URL = url

def start_web_monitoring_session(session_id, session_data, interval):
    """Запуск сессии мониторинга для веб-версии"""
    try:
        user_id = session_data['user_id']
        search_query = session_data['search_query']
        city_code = session_data['city_code']
        city_name = session_data['city_name']
        min_price = session_data.get('min_price')
        max_price = session_data.get('max_price')
        monitoring_time = session_data['monitoring_time']
        
        # Получаем начальные объявления
        parser = AvitoParser()
        initial_ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            price_min=min_price,
            price_max=max_price,
            max_items=50,
            user_id=user_id
        )
        parser.close()
        
        if not initial_ads:
            send_web_notification(user_id, {
                'type': 'error',
                'message': '❌ Не найдено объявлений по вашему запросу. Мониторинг не запущен.'
            })
            return
        
        # Сохраняем ID начальных объявлений
        for ad in initial_ads:
            add_seen_ad(ad['ad_id'], user_id)
        
        update_user_stats(user_id, monitoring_increment=1)
        
        # Отправляем начальный отчет
        send_web_notification(user_id, {
            'type': 'monitoring_started',
            'session_id': session_id,
            'search_query': search_query,
            'city': city_name,
            'initial_count': len(initial_ads),
            'monitoring_time': monitoring_time,
            'interval': interval,
            'message': f'✅ Мониторинг запущен!\n📋 Запрос: {search_query}\n🏙️ Город: {city_name}\n📊 Начальных объявлений: {len(initial_ads)}\n⏰ Завершится через: {monitoring_time} мин'
        })
        
        # Запускаем цикл мониторинга
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=monitoring_time)
        
        while datetime.now() < end_time:
            time.sleep(interval * 60)
            
            if datetime.now() >= end_time:
                break
            
            # Проверяем активность сессии
            try:
                from web_app import active_monitoring_sessions
                if session_id not in active_monitoring_sessions or not active_monitoring_sessions.get(session_id, {}).get('active', True):
                    send_web_notification(user_id, {
                        'type': 'monitoring_stopped',
                        'message': '⏹️ Мониторинг остановлен пользователем'
                    })
                    break
            except:
                pass
            
            try:
                parser = AvitoParser()
                current_ads = parser.parse_avito(
                    search_query=search_query,
                    city_code=city_code,
                    price_min=min_price,
                    price_max=max_price,
                    max_items=50,
                    user_id=user_id
                )
                parser.close()
                
                if not current_ads:
                    continue
                
                # Ищем новые объявления
                new_ads = []
                for ad in current_ads:
                    if not is_ad_seen(ad['ad_id'], user_id):
                        new_ads.append(ad)
                        add_seen_ad(ad['ad_id'], user_id)
                
                # Отправляем уведомления о новых объявлениях
                for ad in new_ads[:5]:
                    notification = f"🆕 *Новое объявление!*\n\n{format_ad_message(ad)}"
                    send_web_notification(user_id, {
                        'type': 'new_ad',
                        'ad': ad,
                        'message': notification
                    })
                    time.sleep(1)
                
                if new_ads:
                    update_user_stats(user_id, ads_increment=len(new_ads))
                    send_web_notification(user_id, {
                        'type': 'stats_update',
                        'new_ads_count': len(new_ads)
                    })
                
            except Exception as e:
                print(f"Ошибка в цикле мониторинга: {e}")
                continue
        
        # Завершаем мониторинг
        send_web_notification(user_id, {
            'type': 'monitoring_completed',
            'message': f'⏹️ Мониторинг завершен!\n\n📋 Запрос: {search_query}\n🏙️ Город: {city_name}\n⏰ Время работы: {monitoring_time} минут'
        })
        
        # Удаляем сессию
        try:
            from web_app import active_monitoring_sessions
            if session_id in active_monitoring_sessions:
                del active_monitoring_sessions[session_id]
        except:
            pass
        
    except Exception as e:
        error_msg = f"❌ Ошибка запуска мониторинга: {str(e)}"
        send_web_notification(session_data.get('user_id'), {
            'type': 'error',
            'message': error_msg
        })

def send_web_notification(user_id, data):
    """Отправка уведомления через WebSocket или SSE"""
    # Для простоты используем сохранение в БД, а клиент периодически проверяет
    conn = None
    try:
        import sqlite3
        conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                notification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute(
            'INSERT INTO web_notifications (user_id, notification) VALUES (?, ?)',
            (user_id, json.dumps(data))
        )
        conn.commit()
    except Exception as e:
        print(f"Ошибка сохранения уведомления: {e}")
    finally:
        if conn:
            conn.close()