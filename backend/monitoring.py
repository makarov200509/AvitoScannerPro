import time
import threading
import sqlite3
import json
from datetime import datetime, timedelta
from parser import AvitoParser
from database import update_user_stats, add_seen_ad, is_ad_seen, save_monitoring_session

_active_sessions_ref = None

def set_active_sessions_ref(ref):
    global _active_sessions_ref
    _active_sessions_ref = ref


def is_session_active(session_id):
    if _active_sessions_ref is not None:
        session = _active_sessions_ref.get(session_id)
        if session:
            if session.get('stopped', False):
                return False
            if not session.get('active', True):
                return False
            if session.get('type') == 'monitoring' and session.get('end_time'):
                try:
                    end_time = datetime.fromisoformat(session['end_time'])
                    if datetime.now() >= end_time:
                        return False
                except:
                    pass
            return True
    return False


def send_web_notification(user_id, data):
    conn = None
    try:
        if data.get('type') != 'new_ad':
            return
        
        conn = sqlite3.connect('avito_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_notifications (
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
        
        ad = data.get('ad', {})
        notification_data = {
            'type': 'new_ad',
            'ad': ad,
            'search_query': data.get('search_query', ''),
            'city': data.get('city', '')
        }
        
        cursor.execute('''
            INSERT INTO web_notifications 
            (user_id, monitoring_session_id, search_query, city, notification) 
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('session_id', ''),
            data.get('search_query', ''),
            data.get('city', ''),
            json.dumps(notification_data, ensure_ascii=False)
        ))
        conn.commit()
        print(f"[NOTIFICATION] New ad for user {user_id}: {ad.get('title', '')[:50]}")
    except Exception as e:
        print(f"Ошибка сохранения веб-уведомления: {e}")
    finally:
        if conn:
            conn.close()


def start_web_monitoring_session(session_id, session_data, interval):
    try:
        user_id = session_data['user_id']
        search_query = session_data['query']
        city_code = session_data['city_code']
        city_name = session_data['city']
        min_price = session_data.get('min_price')
        max_price = session_data.get('max_price')
        monitoring_time = session_data['monitoring_time']
        
        print(f"[MONITORING] Starting monitoring for user {user_id}: {search_query}")
        
        def is_active():
            return is_session_active(session_id)
        
        if not is_active():
            print(f"[MONITORING] Session {session_id} not active, aborting start")
            return
        
        parser = AvitoParser()
        initial_ads = parser.parse_avito(
            search_query=search_query,
            city_code=city_code,
            price_min=min_price,
            price_max=max_price,
            max_items=50,
            user_id=user_id,
            check_active_callback=is_active
        )
        parser.close()
        
        if not is_active():
            print(f"[MONITORING] Session {session_id} became inactive, aborting")
            return
        
        if not initial_ads:
            print(f"[MONITORING] No initial ads found for {search_query}")
            if _active_sessions_ref and session_id in _active_sessions_ref:
                del _active_sessions_ref[session_id]
            return
        
        for ad in initial_ads:
            add_seen_ad(ad['ad_id'], user_id)
        
        save_monitoring_session(
            user_id, search_query, city_name, min_price, max_price,
            monitoring_time, [ad['ad_id'] for ad in initial_ads]
        )
        
        update_user_stats(user_id, monitoring_increment=1)
        
        print(f"[MONITORING] Started. Initial ads: {len(initial_ads)}")
        
        thread = threading.Thread(
            target=run_monitoring_loop,
            args=(session_id, user_id, search_query, city_code, city_name, 
                  min_price, max_price, monitoring_time, interval)
        )
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        error_msg = f"Error starting web monitoring: {str(e)}"
        print(error_msg)
        if _active_sessions_ref and session_id in _active_sessions_ref:
            del _active_sessions_ref[session_id]


def run_monitoring_loop(session_id, user_id, search_query, city_code, city_name, 
                        min_price, max_price, monitoring_time, interval):
    try:
        parser = AvitoParser()
        total_new_ads = 0
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=monitoring_time)
        
        if _active_sessions_ref and session_id in _active_sessions_ref:
            _active_sessions_ref[session_id]['end_time'] = end_time.isoformat()
        
        print(f"[MONITORING] Loop started for session {session_id}, will run until {end_time}")
        
        while datetime.now() < end_time:
            if not is_session_active(session_id):
                print(f"[MONITORING] Session {session_id} stopped by user (before sleep)")
                break
            
            sleep_seconds = interval * 60
            slept = 0
            check_interval = 5 
            
            while slept < sleep_seconds:
                if not is_session_active(session_id):
                    print(f"[MONITORING] Session {session_id} stopped during sleep")
                    break
                time.sleep(min(check_interval, sleep_seconds - slept))
                slept += check_interval
            
            if not is_session_active(session_id):
                break
            
            if datetime.now() >= end_time:
                print(f"[MONITORING] Monitoring time ended for session {session_id}")
                break
            
            try:
                print(f"[MONITORING] Checking for new ads...")
                
                def is_active():
                    return is_session_active(session_id)
                
                current_ads = parser.parse_avito(
                    search_query=search_query,
                    city_code=city_code,
                    price_min=min_price,
                    price_max=max_price,
                    max_items=50,
                    user_id=user_id,
                    check_active_callback=is_active
                )
                
                if not is_session_active(session_id):
                    print(f"[MONITORING] Session {session_id} became inactive during parsing")
                    break
                
                if not current_ads:
                    print(f"[MONITORING] No ads found")
                    continue
                
                new_ads = []
                for ad in current_ads:
                    if not is_ad_seen(ad['ad_id'], user_id):
                        new_ads.append(ad)
                        add_seen_ad(ad['ad_id'], user_id)
                        print(f"[MONITORING] New ad found: {ad['title'][:50]}...")
                
                if new_ads:
                    total_new_ads += len(new_ads)
                    print(f"[MONITORING] Found {len(new_ads)} new ads for {search_query}")
                    
                    for ad in new_ads:
                        if not is_session_active(session_id):
                            break
                        send_web_notification(user_id, {
                            'type': 'new_ad',
                            'session_id': session_id,
                            'search_query': search_query,
                            'city': city_name,
                            'ad': ad
                        })
                        time.sleep(0.5)
                    
                    update_user_stats(user_id, ads_increment=len(new_ads))
                
            except Exception as e:
                print(f"[MONITORING] Error in monitoring loop: {e}")
                continue
        
        parser.close()
        
        print(f"[MONITORING] Monitoring finished for session {session_id}, total new ads: {total_new_ads}")
        
    except Exception as e:
        print(f"[MONITORING] Fatal error in monitoring loop: {e}")
    finally:
        if _active_sessions_ref and session_id in _active_sessions_ref:
            del _active_sessions_ref[session_id]


def get_active_monitoring_sessions(user_id=None):
    if _active_sessions_ref is None:
        return {}
    
    if user_id:
        sessions = {}
        for sid, data in _active_sessions_ref.items():
            if data.get('user_id') == user_id and data.get('type') == 'monitoring' and data.get('active', True):
                sessions[sid] = data
        return sessions
    return {sid: data for sid, data in _active_sessions_ref.items() if data.get('type') == 'monitoring' and data.get('active', True)}


def stop_all_user_monitoring(user_id):
    if _active_sessions_ref is None:
        return 0
    
    stopped_count = 0
    for sid, data in list(_active_sessions_ref.items()):
        if data.get('user_id') == user_id and data.get('type') == 'monitoring' and data.get('active', True):
            _active_sessions_ref[sid]['active'] = False
            _active_sessions_ref[sid]['stopped'] = True
            stopped_count += 1
    
    return stopped_count