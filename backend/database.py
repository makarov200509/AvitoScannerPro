import sqlite3
import json
from datetime import datetime, timedelta
import hashlib
import secrets

def init_db():
    """Инициализация базы данных и создание таблиц"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            telegram_id INTEGER UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Таблица сессий пользователей (для веб-версии)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions_web (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Таблица просмотренных объявлений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id TEXT UNIQUE,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица сессий пользователей (для бота)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            search_query TEXT,
            city TEXT,
            price_min INTEGER,
            price_max INTEGER,
            monitoring_time INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица сессий мониторинга
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            search_query TEXT,
            city TEXT,
            price_min INTEGER,
            price_max INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            initial_ads TEXT
        )
    ''')
    
    # Таблица статистики пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            searches_count INTEGER DEFAULT 0,
            ads_found INTEGER DEFAULT 0,
            monitoring_sessions INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица подписок пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            user_id INTEGER PRIMARY KEY,
            subscription_type TEXT DEFAULT 'free',
            subscription_end TIMESTAMP,
            telegram_payment_charge_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица временных данных пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_temp_data (
            user_id INTEGER PRIMARY KEY,
            temp_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def create_user(username, password, telegram_id=None):
    """Создание нового пользователя (без email)"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, telegram_id)
            VALUES (?, ?, ?)
        ''', (username, password_hash, telegram_id))
        conn.commit()
        user_id = cursor.lastrowid
        
        # Создаем статистику для пользователя
        cursor.execute('''
            INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)
        ''', (user_id,))
        conn.commit()
        
        conn.close()
        return user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        if 'username' in str(e):
            raise ValueError("Пользователь с таким именем уже существует")
        else:
            raise ValueError("Ошибка при создании пользователя")


def authenticate_user(username, password):
    """Аутентификация пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute('''
        SELECT id, username, telegram_id, is_active
        FROM users 
        WHERE username = ? AND password_hash = ? AND is_active = 1
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'telegram_id': user[2],
            'is_active': user[3]
        }
    return None


def create_session(user_id, ip_address=None, user_agent=None):
    """Создание сессии для пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=7)
    
    cursor.execute('''
        INSERT INTO user_sessions_web (user_id, session_token, expires_at, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, session_token, expires_at, ip_address, user_agent))
    
    conn.commit()
    conn.close()
    
    return session_token


def get_session(session_token):
    """Получение сессии по токену"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.user_id, s.session_token, s.expires_at, u.username, u.telegram_id
        FROM user_sessions_web s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
    ''', (session_token,))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return {
            'id': session[0],
            'user_id': session[1],
            'session_token': session[2],
            'expires_at': session[3],
            'username': session[4],
            'telegram_id': session[5]
        }
    return None


def delete_session(session_token):
    """Удаление сессии (выход)"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_sessions_web WHERE session_token = ?', (session_token,))
    conn.commit()
    conn.close()


def delete_all_user_sessions(user_id, current_session_token=None):
    """Удаление всех сессий пользователя (кроме текущей)"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    if current_session_token:
        cursor.execute('DELETE FROM user_sessions_web WHERE user_id = ? AND session_token != ?', 
                      (user_id, current_session_token))
    else:
        cursor.execute('DELETE FROM user_sessions_web WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()


def update_user_last_login(user_id):
    """Обновление времени последнего входа"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    """Получение пользователя по ID"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, telegram_id, created_at, last_login FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'telegram_id': user[2],
            'created_at': user[3],
            'last_login': user[4]
        }
    return None


def get_user_by_telegram_id(telegram_id):
    """Получение пользователя по Telegram ID"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, telegram_id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'telegram_id': user[2]
        }
    return None


def link_telegram_to_user(user_id, telegram_id):
    """Привязка Telegram аккаунта к пользователю"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET telegram_id = ? WHERE id = ?', (telegram_id, user_id))
    conn.commit()
    conn.close()


def update_user_stats(user_id, searches_increment=0, ads_increment=0, monitoring_increment=0):
    """Обновление статистики пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_stats 
        (user_id, searches_count, ads_found, monitoring_sessions, last_active) 
        VALUES (?, COALESCE((SELECT searches_count FROM user_stats WHERE user_id = ?), 0) + ?,
                COALESCE((SELECT ads_found FROM user_stats WHERE user_id = ?), 0) + ?,
                COALESCE((SELECT monitoring_sessions FROM user_stats WHERE user_id = ?), 0) + ?,
                CURRENT_TIMESTAMP)
    ''', (user_id, user_id, searches_increment, user_id, ads_increment, user_id, monitoring_increment))
    
    conn.commit()
    conn.close()


def add_user_subscription(user_id, subscription_type, days, charge_id):
    """Добавление или обновление подписки пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    subscription_end = datetime.now() + timedelta(days=days)
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_subscriptions 
        (user_id, subscription_type, subscription_end, telegram_payment_charge_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, subscription_type, subscription_end, charge_id))
    
    conn.commit()
    conn.close()


def check_user_subscription(user_id):
    """Проверка активной подписки пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT subscription_type, subscription_end 
        FROM user_subscriptions 
        WHERE user_id = ? AND subscription_end > CURRENT_TIMESTAMP
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        end_date = result[1]
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_date = datetime.now() + timedelta(days=1)
        
        return {
            'type': result[0],
            'end_date': end_date,
            'active': True
        }
    return {'active': False}


def save_user_temp_data(user_id, temp_data):
    """Сохранение временных данных пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_temp_data 
        (user_id, temp_data) 
        VALUES (?, ?)
    ''', (user_id, json.dumps(temp_data)))
    
    conn.commit()
    conn.close()


def get_user_temp_data(user_id):
    """Получение временных данных пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('SELECT temp_data FROM user_temp_data WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return json.loads(result[0])
    return None


def delete_user_temp_data(user_id):
    """Удаление временных данных пользователя"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM user_temp_data WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def save_monitoring_session(user_id, search_query, city, price_min, price_max, end_time, initial_ads):
    """Сохранение сессии мониторинга"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO monitoring_sessions 
        (user_id, search_query, city, price_min, price_max, end_time, initial_ads)
        VALUES (?, ?, ?, ?, ?, datetime(CURRENT_TIMESTAMP, ?), ?)
    ''', (user_id, search_query, city, price_min, price_max, f'+{end_time} minutes', json.dumps(initial_ads)))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def add_seen_ad(ad_id, user_id):
    """Добавление просмотренного объявления"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO seen_ads (ad_id, user_id) VALUES (?, ?)',
            (ad_id, user_id)
        )
        conn.commit()
    except:
        pass
    finally:
        conn.close()


def is_ad_seen(ad_id, user_id):
    """Проверка, было ли объявление уже просмотрено"""
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT 1 FROM seen_ads WHERE ad_id = ? AND user_id = ?',
        (ad_id, user_id)
    )
    result = cursor.fetchone()
    conn.close()
    
    return result is not None