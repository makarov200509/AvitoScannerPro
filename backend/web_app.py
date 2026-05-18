from dotenv import load_dotenv
load_dotenv()
from flask import Flask, send_from_directory, request, jsonify, send_file, make_response, session
from flask_cors import CORS
import threading
import sqlite3
import json
from datetime import datetime, timedelta
import secrets
import os
from parser import AvitoParser
from database import (
    update_user_stats,
    add_seen_ad, is_ad_seen, save_monitoring_session, init_db,
    create_user, authenticate_user, create_session, get_session, delete_session,
    delete_all_user_sessions, update_user_last_login, get_user_by_id
)
from utils import calculate_price_statistics, format_price, find_city_code
import uuid
from functools import wraps
import atexit
from parser import shutdown_parser_pool
import bcrypt

app = Flask(__name__, static_folder='static/dist', static_url_path='')

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError('SECRET_KEY environment variable is not set in production!')
    else:
        print("WARNING: Using temporary secret key. Set SECRET_KEY environment variable for production!")
        SECRET_KEY = secrets.token_hex(32)

app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)

active_sessions = {}
search_results_store = {}
MAX_PROCESSES_PER_USER = 7

TIME_OFFSET_HOURS = 3

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token():
    token = request.headers.get('X-CSRF-Token')
    if not token:
        return False
    return token == session.get('csrf_token')

def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if not validate_csrf_token():
                return jsonify({'error': 'CSRF token validation failed'}), 403
        return f(*args, **kwargs)
    return decorated_function

def fix_time(timestamp):
    if not timestamp:
        return timestamp
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        dt = dt + timedelta(hours=TIME_OFFSET_HOURS)
        return dt.isoformat() if isinstance(timestamp, str) else dt
    except:
        return timestamp

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'error': 'Не авторизован', 'redirect': '/login'}), 401
        
        user_session = get_session(session_token)
        if not user_session:
            return jsonify({'error': 'Сессия истекла', 'redirect': '/login'}), 401
        
        request.user = user_session
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    user_session = get_session(session_token)
    return user_session['user_id'] if user_session else None

def init_web_db():
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='web_notifications'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        cursor.execute('''
            CREATE TABLE web_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                monitoring_session_id TEXT,
                search_query TEXT,
                city TEXT,
                notification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            )
        ''')
        print("Создана таблица web_notifications")
    else:
        cursor.execute("PRAGMA table_info(web_notifications)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        if 'monitoring_session_id' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN monitoring_session_id TEXT')
            print("Добавлен столбец monitoring_session_id")
        
        if 'search_query' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN search_query TEXT')
            print("Добавлен столбец search_query")
        
        if 'city' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN city TEXT')
            print("Добавлен столбец city")
        
        if 'is_read' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN is_read INTEGER DEFAULT 0')
            print("Добавлен столбец is_read")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_id INTEGER,
            search_query TEXT,
            city TEXT,
            min_price INTEGER,
            max_price INTEGER,
            results_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            ad_id TEXT,
            title TEXT,
            price TEXT,
            link TEXT,
            date TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_id INTEGER,
            search_query TEXT,
            city TEXT,
            results_count INTEGER DEFAULT 0,
            median_price INTEGER,
            mean_price REAL,
            min_price INTEGER,
            max_price INTEGER,
            ads_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            process_type TEXT,
            search_query TEXT,
            city TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            searches_count INTEGER DEFAULT 0,
            ads_found INTEGER DEFAULT 0,
            monitoring_sessions INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Таблицы созданы/проверены")

init_db()
init_web_db()

def migrate_db():
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(analysis_history)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'results_count' not in columns:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN results_count INTEGER DEFAULT 0')
    
    if 'median_price' not in columns:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN median_price INTEGER')
    
    if 'mean_price' not in columns:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN mean_price REAL')
    
    if 'min_price' not in columns:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN min_price INTEGER')
    
    if 'max_price' not in columns:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN max_price INTEGER')
    
    if 'ads_data' not in columns:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN ads_data TEXT')
    
    cursor.execute("PRAGMA table_info(search_history)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'min_price' not in columns:
        cursor.execute('ALTER TABLE search_history ADD COLUMN min_price INTEGER')
    
    if 'max_price' not in columns:
        cursor.execute('ALTER TABLE search_history ADD COLUMN max_price INTEGER')
    
    cursor.execute("PRAGMA table_info(user_stats)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'searches_count' not in columns:
        cursor.execute('ALTER TABLE user_stats ADD COLUMN searches_count INTEGER DEFAULT 0')
    if 'ads_found' not in columns:
        cursor.execute('ALTER TABLE user_stats ADD COLUMN ads_found INTEGER DEFAULT 0')
    if 'monitoring_sessions' not in columns:
        cursor.execute('ALTER TABLE user_stats ADD COLUMN monitoring_sessions INTEGER DEFAULT 0')
    
    conn.commit()
    conn.close()
    print("Миграция базы данных завершена")

migrate_db()

def save_analysis_to_db(session_id, user_id, search_query, city, ads, stats):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO analysis_history 
        (session_id, user_id, search_query, city, results_count, median_price, mean_price, min_price, max_price, ads_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, user_id, search_query, city, len(ads),
        stats.get('median'), stats.get('mean'), stats.get('min'), stats.get('max'),
        json.dumps(ads[:400], ensure_ascii=False)
    ))
    
    conn.commit()
    conn.close()

def get_user_analysis_history(user_id, limit=20):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT session_id, search_query, city, results_count, created_at
            FROM analysis_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'session_id': row[0],
                'search_query': row[1],
                'city': row[2],
                'results_count': row[3],
                'created_at': fix_time(row[4]) if row[4] else row[4]
            })
    except sqlite3.OperationalError as e:
        print(f"Ошибка в get_user_analysis_history: {e}")
        history = []
    
    conn.close()
    return history

def get_analysis_by_session(session_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT search_query, city, results_count, median_price, mean_price, min_price, max_price, ads_data
            FROM analysis_history
            WHERE session_id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            ads = json.loads(row[7]) if row[7] else []
            return {
                'search_query': row[0],
                'city': row[1],
                'ads_count': row[2],
                'stats': {
                    'median': row[3],
                    'mean': row[4],
                    'min': row[5],
                    'max': row[6]
                },
                'ads': ads
            }
    except sqlite3.OperationalError as e:
        print(f"Ошибка в get_analysis_by_session: {e}")
        conn.close()
    
    return None

def delete_analysis_session(session_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM analysis_history WHERE session_id = ? AND user_id = ?', (session_id, user_id))
    conn.commit()
    conn.close()

def save_search_results_to_db(session_id, user_id, search_query, city, min_price, max_price, ads):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO search_history 
        (session_id, user_id, search_query, city, min_price, max_price, results_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, user_id, search_query, city, min_price, max_price, len(ads)))
    
    for ad in ads:
        cursor.execute('''
            INSERT OR IGNORE INTO search_results 
            (session_id, user_id, ad_id, title, price, link, date, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, ad['ad_id'], ad['title'], ad['price'], ad['link'], ad['date'], ad['location']))
    
    conn.commit()
    conn.close()

def get_user_search_history(user_id, limit=20):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT session_id, search_query, city, min_price, max_price, results_count, created_at
        FROM search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            'session_id': row[0],
            'search_query': row[1],
            'city': row[2],
            'min_price': row[3],
            'max_price': row[4],
            'results_count': row[5],
            'created_at': fix_time(row[6]) if row[6] else row[6]
        })
    
    conn.close()
    return history

def get_search_results_by_session(session_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ad_id, title, price, link, date, location
        FROM search_results
        WHERE session_id = ? AND user_id = ?
        ORDER BY created_at
    ''', (session_id, user_id))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'ad_id': row[0],
            'title': row[1],
            'price': row[2],
            'link': row[3],
            'date': row[4],
            'location': row[5]
        })
    
    conn.close()
    return results

def delete_search_session(session_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM search_history WHERE session_id = ? AND user_id = ?', (session_id, user_id))
    cursor.execute('DELETE FROM search_results WHERE session_id = ? AND user_id = ?', (session_id, user_id))
    conn.commit()
    conn.close()

def get_user_active_processes_count(user_id):
    count = 0
    for session_id, session_data in active_sessions.items():
        if session_data.get('user_id') == user_id and session_data.get('active', True):
            if session_data.get('type') == 'monitoring' and session_data.get('end_time'):
                try:
                    end_time = datetime.fromisoformat(session_data['end_time'])
                    if datetime.now() >= end_time:
                        continue
                except:
                    pass
            count += 1
    return count

def add_process_to_history(user_id, session_id, process_type, search_query, city):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO process_history (session_id, user_id, process_type, search_query, city, status)
        VALUES (?, ?, ?, ?, ?, 'active')
    ''', (session_id, user_id, process_type, search_query, city))
    conn.commit()
    conn.close()

def update_process_history(session_id, status='completed'):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE process_history 
        SET ended_at = CURRENT_TIMESTAMP, status = ?
        WHERE session_id = ?
    ''', (status, session_id))
    conn.commit()
    conn.close()

def remove_session(session_id):
    if session_id in active_sessions:
        session_data = active_sessions[session_id]
        update_process_history(session_id, 'stopped' if session_data.get('active') is False else 'completed')
        del active_sessions[session_id]

def delete_single_notification(notification_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM web_notifications WHERE id = ? AND user_id = ?', (notification_id, user_id))
    conn.commit()
    conn.close()

def delete_session_notifications(monitoring_session_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM web_notifications WHERE monitoring_session_id = ? AND user_id = ?', (monitoring_session_id, user_id))
    conn.commit()
    conn.close()

def send_web_notification(user_id, data):
    conn = None
    try:
        if data.get('type') != 'new_ad':
            return
        
        conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(web_notifications)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        if 'monitoring_session_id' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN monitoring_session_id TEXT')
        if 'search_query' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN search_query TEXT')
        if 'city' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN city TEXT')
        if 'is_read' not in existing_columns:
            cursor.execute('ALTER TABLE web_notifications ADD COLUMN is_read INTEGER DEFAULT 0')
        
        ad = data.get('ad', {})
        notification_data = {
            'type': 'new_ad',
            'ad': ad,
            'search_query': data.get('search_query', ''),
            'city': data.get('city', '')
        }
        
        cursor.execute('''
            INSERT INTO web_notifications 
            (user_id, monitoring_session_id, search_query, city, notification, is_read) 
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (
            user_id,
            data.get('session_id', ''),
            data.get('search_query', ''),
            data.get('city', ''),
            json.dumps(notification_data, ensure_ascii=False)
        ))
        conn.commit()
        print(f"[УВЕДОМЛЕНИЕ] Новое объявление для пользователя {user_id}: {ad.get('title', '')[:50]}")
    except Exception as e:
        print(f"Ошибка сохранения уведомления: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/api/csrf-token', methods=['GET'])
@login_required
def get_csrf_token():
    token = generate_csrf_token()
    return jsonify({'csrf_token': token})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip() if data.get('username') else ''
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Имя пользователя и пароль обязательны'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Имя пользователя должно содержать минимум 3 символа'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Пароль должен содержать минимум 4 символа'}), 400
    
    try:
        user_id = create_user(username, password)
        return jsonify({'success': True, 'message': 'Регистрация успешна! Теперь войдите.'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Введите имя пользователя и пароль'}), 400
    
    user = authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401
    
    session_token = create_session(
        user['id'],
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    update_user_last_login(user['id'])
    
    response = jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username']
        }
    })
    
    is_secure = os.environ.get('FLASK_ENV') == 'production'
    response.set_cookie(
        'session_token', 
        session_token, 
        httponly=True, 
        secure=is_secure,
        samesite='Strict',
        max_age=7*24*3600
    )
    return response

@app.route('/api/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        delete_session(session_token)
    response = jsonify({'success': True})
    response.delete_cookie('session_token')
    return response

@app.route('/api/me', methods=['GET'])
def get_me():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return jsonify({'authenticated': False}), 200
    
    user_session = get_session(session_token)
    if not user_session:
        response = jsonify({'authenticated': False})
        response.delete_cookie('session_token')
        return response, 200
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': user_session['user_id'],
            'username': user_session['username']
        }
    })

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return jsonify({'authenticated': False})
    
    user_session = get_session(session_token)
    if not user_session:
        return jsonify({'authenticated': False})
    
    return jsonify({'authenticated': True, 'username': user_session['username']})

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/register.html')
def register_page():
    return send_from_directory(app.static_folder, 'register.html')

@app.route('/api/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    user_id = request.user['user_id']
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT searches_count, ads_found, monitoring_sessions FROM user_stats WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    active_count = get_user_active_processes_count(user_id)
    
    if result:
        return jsonify({
            'searches_count': result[0] or 0,
            'ads_found': result[1] or 0,
            'monitoring_sessions': result[2] or 0,
            'active_processes': active_count,
            'max_processes': MAX_PROCESSES_PER_USER
        })
    return jsonify({
        'searches_count': 0,
        'ads_found': 0,
        'monitoring_sessions': 0,
        'active_processes': active_count,
        'max_processes': MAX_PROCESSES_PER_USER
    })

@app.route('/api/search-history', methods=['GET'])
@login_required
def get_search_history():
    user_id = request.user['user_id']
    history = get_user_search_history(user_id)
    return jsonify({'history': history})

@app.route('/api/search-history/<session_id>/results', methods=['GET'])
@login_required
def get_search_history_results(session_id):
    user_id = request.user['user_id']
    results = get_search_results_by_session(session_id, user_id)
    return jsonify({'results': results, 'session_id': session_id})

@app.route('/api/search-history/<session_id>', methods=['DELETE'])
@login_required
@csrf_protect
def delete_search_history(session_id):
    user_id = request.user['user_id']
    delete_search_session(session_id, user_id)
    return jsonify({'success': True})

@app.route('/api/analysis-history', methods=['GET'])
@login_required
def get_analysis_history():
    user_id = request.user['user_id']
    history = get_user_analysis_history(user_id)
    return jsonify({'history': history})

@app.route('/api/analysis-history/<session_id>/results', methods=['GET'])
@login_required
def get_analysis_history_results(session_id):
    user_id = request.user['user_id']
    results = get_analysis_by_session(session_id, user_id)
    return jsonify({'results': results, 'session_id': session_id})

@app.route('/api/analysis-history/<session_id>', methods=['DELETE'])
@login_required
@csrf_protect
def delete_analysis_history(session_id):
    user_id = request.user['user_id']
    delete_analysis_session(session_id, user_id)
    return jsonify({'success': True})

@app.route('/api/active-processes', methods=['GET'])
@login_required
def get_active_processes():
    user_id = request.user['user_id']
    processes = []
    for session_id, session_data in active_sessions.items():
        if session_data.get('user_id') == user_id and session_data.get('active', True):
            if session_data.get('type') == 'monitoring' and session_data.get('end_time'):
                try:
                    end_time = datetime.fromisoformat(session_data['end_time'])
                    if datetime.now() >= end_time:
                        continue
                except:
                    pass
            
            processes.append({
                'id': session_id,
                'type': session_data.get('type'),
                'query': session_data.get('query'),
                'city': session_data.get('city'),
                'startedAt': session_data.get('started_at'),
                'endTime': session_data.get('end_time'),
                'minPrice': session_data.get('min_price'),
                'maxPrice': session_data.get('max_price')
            })
    
    return jsonify({'processes': processes})

@app.route('/api/process/stop/<session_id>', methods=['POST'])
@login_required
@csrf_protect
def stop_process(session_id):
    user_id = request.user['user_id']
    if session_id in active_sessions and active_sessions[session_id].get('user_id') == user_id:
        active_sessions[session_id]['active'] = False
        active_sessions[session_id]['stopped'] = True
        update_process_history(session_id, 'stopped')
        return jsonify({'success': True, 'message': 'Процесс остановлен'})
    return jsonify({'success': False, 'error': 'Процесс не найден'}), 404

@app.route('/api/process/stop-all', methods=['POST'])
@login_required
@csrf_protect
def stop_all_processes():
    user_id = request.user['user_id']
    stopped = []
    for session_id, session_data in list(active_sessions.items()):
        if session_data.get('user_id') == user_id and session_data.get('active', True):
            session_data['active'] = False
            session_data['stopped'] = True
            update_process_history(session_id, 'stopped')
            stopped.append(session_id)
    return jsonify({'success': True, 'stopped_count': len(stopped)})

@app.route('/api/search', methods=['POST'])
@login_required
@csrf_protect
def search():
    data = request.json
    user_id = request.user['user_id']
    search_query = data.get('search_query')
    city_input = data.get('city')
    min_price = data.get('min_price')
    max_price = data.get('max_price')
    
    if not search_query:
        return jsonify({'error': 'Пустой поисковый запрос'}), 400

    active_count = get_user_active_processes_count(user_id)
    if active_count >= MAX_PROCESSES_PER_USER:
        return jsonify({
            'success': False,
            'error': f'Достигнуто максимальное количество одновременных процессов ({MAX_PROCESSES_PER_USER})'
        }), 429
    
    city_code, city_name = find_city_code(city_input if city_input else 'Все регионы')
    
    session_id = str(uuid.uuid4())
    session_data = {
        'user_id': user_id,
        'type': 'search',
        'query': search_query,
        'city': city_name,
        'started_at': datetime.now().isoformat(),
        'active': True,
        'stopped': False
    }
    active_sessions[session_id] = session_data
    add_process_to_history(user_id, session_id, 'search', search_query, city_name)
    
    thread = threading.Thread(
        target=perform_search_task,
        args=(session_id, user_id, search_query, city_code, city_name, min_price, max_price)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': f'Поиск запущен. Активных процессов: {active_count + 1}/{MAX_PROCESSES_PER_USER}'
    })

def is_session_active_check(session_id):
    session = active_sessions.get(session_id)
    if not session:
        return False
    if session.get('stopped', False):
        return False
    if not session.get('active', True):
        return False
    return True

def perform_search_task(session_id, user_id, search_query, city_code, city_name, min_price, max_price):
    try:
        def is_active():
            return is_session_active_check(session_id)
        
        parser = AvitoParser()
        ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            price_min=min_price,
            price_max=max_price,
            max_items=50,
            user_id=user_id,
            pages=1,
            check_active_callback=is_active
        )
        parser.close()
        
        if not is_active():
            print(f"[ПОИСК] Сессия {session_id} остановлена, результаты не сохраняются")
            return
        
        update_user_stats(user_id, searches_increment=1, ads_increment=len(ads) if ads else 0)
        save_search_results_to_db(session_id, user_id, search_query, city_name, min_price, max_price, ads or [])
        
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    finally:
        if session_id in active_sessions:
            if is_session_active_check(session_id):
                update_process_history(session_id, 'completed')
            else:
                update_process_history(session_id, 'stopped')
            del active_sessions[session_id]

def get_analysis_all_ads(session_id, user_id):
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT ads_data
            FROM analysis_history
            WHERE session_id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            ads = json.loads(row[0]) if row[0] else []
            return ads
    except sqlite3.OperationalError as e:
        print(f"Ошибка в get_analysis_all_ads: {e}")
        conn.close()
    
    return []

@app.route('/api/market-analysis', methods=['POST'])
@login_required
@csrf_protect
def market_analysis():
    data = request.json
    user_id = request.user['user_id']
    search_query = data.get('search_query')
    city_input = data.get('city')
    
    if not search_query:
        return jsonify({'error': 'Пустой поисковый запрос'}), 400
    
    active_count = get_user_active_processes_count(user_id)
    if active_count >= MAX_PROCESSES_PER_USER:
        return jsonify({
            'success': False,
            'error': f'Достигнуто максимальное количество одновременных процессов ({MAX_PROCESSES_PER_USER})'
        }), 429
    
    city_code, city_name = find_city_code(city_input if city_input else 'Все регионы')
    
    session_id = str(uuid.uuid4())
    session_data = {
        'user_id': user_id,
        'type': 'analysis',
        'query': search_query,
        'city': city_name,
        'started_at': datetime.now().isoformat(),
        'active': True,
        'stopped': False
    }
    active_sessions[session_id] = session_data
    add_process_to_history(user_id, session_id, 'analysis', search_query, city_name)
    
    thread = threading.Thread(
        target=perform_analysis_task,
        args=(session_id, user_id, search_query, city_code, city_name)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': f'Анализ запущен. Активных процессов: {active_count + 1}/{MAX_PROCESSES_PER_USER}'
    })

def perform_analysis_task(session_id, user_id, search_query, city_code, city_name):
    try:
        def is_active():
            return is_session_active_check(session_id)
        
        parser = AvitoParser()
        ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            max_items=400,
            user_id=user_id,
            pages=8,
            check_active_callback=is_active
        )
        parser.close()
        
        if not is_active():
            print(f"[АНАЛИЗ] Сессия {session_id} остановлена, результаты не сохраняются")
            return
        
        if ads:
            stats = calculate_price_statistics(ads)
            if stats:
                update_user_stats(user_id, searches_increment=1, ads_increment=len(ads))
                save_analysis_to_db(session_id, user_id, search_query, city_name, ads, stats)
        
    except Exception as e:
        print(f"Ошибка анализа: {e}")
    finally:
        if session_id in active_sessions:
            if is_session_active_check(session_id):
                update_process_history(session_id, 'completed')
            else:
                update_process_history(session_id, 'stopped')
            del active_sessions[session_id]

@app.route('/api/analysis-history/<session_id>/all-ads', methods=['GET'])
@login_required
def get_analysis_all_ads_route(session_id):
    user_id = request.user['user_id']
    ads = get_analysis_all_ads(session_id, user_id)
    return jsonify({'ads': ads, 'session_id': session_id})

@app.route('/api/monitoring/start', methods=['POST'])
@login_required
@csrf_protect
def start_monitoring():
    data = request.json
    user_id = request.user['user_id']
    search_query = data.get('search_query')
    city_input = data.get('city')
    min_price = data.get('min_price')
    max_price = data.get('max_price')
    monitoring_time = data.get('monitoring_time', 60)
    interval = data.get('interval', 5)
    
    if not search_query:
        return jsonify({'error': 'Пустой поисковый запрос'}), 400
    
    active_count = get_user_active_processes_count(user_id)
    if active_count >= MAX_PROCESSES_PER_USER:
        return jsonify({
            'success': False,
            'error': f'Достигнуто максимальное количество одновременных процессов ({MAX_PROCESSES_PER_USER})'
        }), 429
    
    city_code, city_name = find_city_code(city_input if city_input else 'Все регионы')
    
    session_id = str(uuid.uuid4())
    end_time = datetime.now() + timedelta(minutes=monitoring_time)
    
    session_data = {
        'user_id': user_id,
        'type': 'monitoring',
        'query': search_query,
        'city': city_name,
        'city_code': city_code,
        'min_price': min_price,
        'max_price': max_price,
        'monitoring_time': monitoring_time,
        'interval': interval,
        'started_at': datetime.now().isoformat(),
        'end_time': end_time.isoformat(),
        'active': True,
        'stopped': False
    }
    
    active_sessions[session_id] = session_data
    add_process_to_history(user_id, session_id, 'monitoring', search_query, city_name)
    
    import monitoring
    monitoring.set_active_sessions_ref(active_sessions)
    
    from monitoring import start_web_monitoring_session
    thread = threading.Thread(
        target=start_web_monitoring_session,
        args=(session_id, session_data, interval)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': f'Мониторинг запущен на {monitoring_time} минут'
    })

@app.route('/api/cities', methods=['GET'])
def get_cities():
    from config import CITIES
    return jsonify(list(CITIES.keys()))

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_web_notifications():
    user_id = request.user['user_id']
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT monitoring_session_id, search_query, city, COUNT(*) as count, MAX(created_at) as last_created
            FROM web_notifications
            WHERE user_id = ? AND monitoring_session_id IS NOT NULL AND monitoring_session_id != ''
            GROUP BY monitoring_session_id, search_query, city
            ORDER BY last_created DESC
        ''', (user_id,))
    except sqlite3.OperationalError as e:
        print(f"Ошибка в запросе: {e}")
        conn.close()
        return jsonify({'sessions': []})
    
    sessions = []
    session_ids = []
    
    for row in cursor.fetchall():
        session_id = row[0]
        session_ids.append({
            'session_id': session_id,
            'search_query': row[1] if row[1] else '',
            'city': row[2] if row[2] else '',
            'count': row[3],
            'last_created': fix_time(row[4]) if row[4] else row[4]
        })
    
    for s in session_ids:
        try:
            cursor.execute('''
                SELECT id, notification, created_at, is_read
                FROM web_notifications
                WHERE user_id = ? AND monitoring_session_id = ?
                ORDER BY created_at DESC
            ''', (user_id, s['session_id']))
        except:
            continue
        
        notifications = []
        
        for row in cursor.fetchall():
            try:
                data = json.loads(row[1]) if row[1] else {}
            except:
                data = {'type': 'new_ad', 'ad': {}}
            
            ad = data.get('ad', {})
            notifications.append({
                'id': row[0],
                'title': ad.get('title', ''),
                'price': ad.get('price', ''),
                'location': ad.get('location', ''),
                'date': ad.get('date', ''),
                'link': ad.get('link', ''),
                'created_at': fix_time(row[2]) if row[2] else row[2],
                'is_read': bool(row[3]) if len(row) > 3 else False
            })
        
        sessions.append({
            'session_id': s['session_id'],
            'search_query': s['search_query'],
            'city': s['city'],
            'count': s['count'],
            'notifications': notifications
        })
    
    conn.close()
    return jsonify({'sessions': sessions})

@app.route('/api/notifications/mark-session-read/<session_id>', methods=['POST'])
@login_required
@csrf_protect
def mark_session_notifications_read(session_id):
    user_id = request.user['user_id']
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE web_notifications 
            SET is_read = 1 
            WHERE user_id = ? AND monitoring_session_id = ? AND is_read = 0
        ''', (user_id, session_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка отметки уведомлений как прочитанных: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/notifications/clear', methods=['POST'])
@login_required
@csrf_protect
def clear_notifications():
    user_id = request.user['user_id']
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM web_notifications WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/notifications/clear-session/<session_id>', methods=['DELETE'])
@login_required
@csrf_protect
def clear_session_notifications_route(session_id):
    user_id = request.user['user_id']
    delete_session_notifications(session_id, user_id)
    return jsonify({'success': True})

@app.route('/api/notifications/delete/<int:notification_id>', methods=['DELETE'])
@login_required
@csrf_protect
def delete_notification_route(notification_id):
    user_id = request.user['user_id']
    delete_single_notification(notification_id, user_id)
    return jsonify({'success': True})

@app.route('/api/process-history', methods=['GET'])
@login_required
def get_process_history():
    user_id = request.user['user_id']
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT session_id, process_type, search_query, city, started_at, ended_at, status
        FROM process_history
        WHERE user_id = ?
        ORDER BY started_at DESC LIMIT 50
    ''', (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    history = []
    for row in results:
        history.append({
            'session_id': row[0],
            'type': row[1],
            'query': row[2],
            'city': row[3],
            'started_at': row[4],
            'ended_at': row[5],
            'status': row[6]
        })
    
    return jsonify({'history': history})

@app.route('/api/avatar')
def get_avatar():
    avatar_path = os.path.join('static/dist', 'avatar.jpg')
    
    if os.path.exists(avatar_path):
        return send_file(avatar_path, mimetype='image/jpeg')
    else:
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="#2563eb">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>'''
        response = make_response(svg)
        response.headers['Content-Type'] = 'image/svg+xml'
        return response

@app.route('/api/change-password', methods=['POST'])
@login_required
@csrf_protect
def change_password():
    user_id = request.user['user_id']
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    if len(new_password) < 4:
        return jsonify({'error': 'Новый пароль должен содержать минимум 4 символа'}), 400
    
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    stored_hash = row[0]
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    
    if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
        conn.close()
        return jsonify({'error': 'Неверный текущий пароль'}), 401
    
    salt = bcrypt.gensalt()
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
    conn.commit()
    conn.close()
    
    delete_all_user_sessions(user_id, request.cookies.get('session_token'))
    
    return jsonify({'success': True, 'message': 'Пароль изменен'})

@app.route('/api/delete-account', methods=['POST'])
@login_required
@csrf_protect
def delete_account():
    user_id = request.user['user_id']
    
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM user_sessions_web WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM user_stats WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM search_history WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM search_results WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM analysis_history WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM process_history WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM web_notifications WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM seen_ads WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM monitoring_sessions WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    response = jsonify({'success': True})
    response.delete_cookie('session_token')
    return response

@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_notifications_count():
    user_id = request.user['user_id']
    conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM web_notifications 
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({'unread_count': count})
    except Exception as e:
        conn.close()
        return jsonify({'unread_count': 0})

@app.route('/api/pool-stats', methods=['GET'])
@login_required
def get_pool_stats():
    from parser import AvitoParser
    parser = AvitoParser()
    stats = parser.get_pool_stats() if hasattr(parser, 'get_pool_stats') else {'message': 'Недоступно'}
    return jsonify(stats)

def cleanup():
    print("Завершение работы пула парсера...")
    shutdown_parser_pool()
    print("Очистка завершена")

atexit.register(cleanup)

if __name__ == '__main__':
    os.makedirs('static/dist', exist_ok=True)
    
    index_path = os.path.join('static/dist', 'index.html')
    if not os.path.exists(index_path):
        print(f"ПРЕДУПРЕЖДЕНИЕ: Файл {index_path} не найден!")
    
    import monitoring
    monitoring.set_active_sessions_ref(active_sessions)
    
    is_secure = os.environ.get('FLASK_ENV') == 'production'
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    try:
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=debug_mode, 
            threaded=True, 
            use_reloader=False,
            ssl_context='adhoc' if is_secure else None
        )
    finally:
        cleanup()