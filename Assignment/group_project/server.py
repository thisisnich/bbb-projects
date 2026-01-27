from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import eventlet
from eventlet import wsgi
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import json
import random
import threading
import time
import base64
import os
import sys
from collections import defaultdict
import sqlite3
from statistics import mean

# AI Image Recognition (Claude API)
ANTHROPIC_AVAILABLE = False
anthropic_client = None

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
    print("[INFO] Anthropic library imported successfully")
except ImportError as e:
    print(f"[WARNING] Failed to import anthropic library: {e}")
    print("[INFO] Install with: pip install anthropic")
    print(f"[DEBUG] Python executable: {sys.executable}")
except Exception as e:
    print(f"[WARNING] Unexpected error importing anthropic: {e}")
    import traceback
    traceback.print_exc()

if ANTHROPIC_AVAILABLE:
    # Get API key from environment variable first, then .env file
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    
    # Try to load from .env file if env var not set
    if not anthropic_api_key:
        try:
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            if line.startswith('ANTHROPIC_API_KEY='):
                                anthropic_api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                                print(f"[INFO] Using API key from .env file (length: {len(anthropic_api_key)})")
                                break
        except Exception as e:
            print(f"[WARNING] Could not read .env file: {e}")
            import traceback
            traceback.print_exc()
    
    if anthropic_api_key:
        try:
            anthropic_client = Anthropic(api_key=anthropic_api_key)
            print(f"[INFO] Anthropic API client initialized successfully (key length: {len(anthropic_api_key)})")
        except Exception as e:
            anthropic_client = None
            print(f"[ERROR] Failed to initialize Anthropic client: {e}")
            import traceback
            traceback.print_exc()
    else:
        anthropic_client = None
        print("[WARNING] ANTHROPIC_API_KEY not set. AI image analysis disabled.")

app = Flask(__name__)
# Set max content length for file uploads (16MB as per documentation)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# Session secret key for authentication
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# User credentials (in production, use a database)
USERS = {
    'guest': {
        'guest1': 'guest123',
        'guest2': 'guest456'
    },
    'personnel': {
        'admin': 'admin123',
        'staff': 'staff123'
    }
}

# Authentication decorator
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

<<<<<<< HEAD
<<<<<<< HEAD
# --- Comprehensive Data Storage System ---
>>>>>>> c668bf5 (Add authentication system with role-based dashboards)
# --- Historical Data Storage ---
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')
HISTORY_DB = os.path.join(os.path.dirname(__file__), 'history.db')
USE_DATABASE = True  # Set to False to use JSON files instead

# Minute-based averaging buffers (collect data for 1 minute, then save average)
minute_buffers = {
    'module1_crowd': [],      # {people_count, noise_db, timestamp}
    'module1_audio': [],      # {noise_db, timestamp}
    'module2_env': [],        # {temperature_c, humidity_percent, pressure_hpa, uv_index, voc_level, comfort_score, timestamp}
    'module3_feedback': []    # {rating, timestamp} - only save when rating occurs
}
buffer_lock = threading.Lock()

# ===== DATABASE FUNCTIONS =====

def init_database():
    """Initialize SQLite database with tables for all modules"""
    if not USE_DATABASE:
        return
    
    try:
        conn = sqlite3.connect(HISTORY_DB)
        cursor = conn.cursor()
        
        # Module 1: Crowd detection (people count)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module1_crowd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                people_count INTEGER,
                noise_db REAL,
                UNIQUE(timestamp)
            )
        ''')
        
        # Module 1: Audio (noise levels)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module1_audio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                noise_db REAL,
                UNIQUE(timestamp)
            )
        ''')
        
        # Module 2: Environment data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module2_environment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature_c REAL,
                humidity_percent REAL,
                pressure_hpa REAL,
                uv_index REAL,
                voc_level TEXT,
                comfort_score REAL,
                UNIQUE(timestamp)
            )
        ''')
        
        # Module 3: Feedback/ratings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module3_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rating INTEGER,
                report_type TEXT,
                UNIQUE(timestamp)
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_module1_crowd_timestamp ON module1_crowd(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_module1_audio_timestamp ON module1_audio(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_module2_env_timestamp ON module2_environment(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_module3_feedback_timestamp ON module3_feedback(timestamp)')
        
        conn.commit()
        conn.close()
        print(f"[INFO] Database initialized: {HISTORY_DB}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()

def save_minute_averages():
    """Save averaged data from minute buffers to database/JSON"""
    global minute_buffers
    
    with buffer_lock:
        now = datetime.now()
        timestamp_str = now.isoformat()
        
        # Module 1: Crowd + Audio
        if minute_buffers['module1_crowd']:
            entries = minute_buffers['module1_crowd']
            avg_people = int(mean([e.get('people_count', 0) for e in entries]))
            avg_noise = mean([e.get('noise_db', 0) for e in entries if e.get('noise_db') is not None]) if any(e.get('noise_db') for e in entries) else None
            
            if USE_DATABASE:
                try:
                    conn = sqlite3.connect(HISTORY_DB)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO module1_crowd (timestamp, people_count, noise_db)
                        VALUES (?, ?, ?)
                    ''', (timestamp_str, avg_people, avg_noise))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[ERROR] Failed to save Module 1 crowd data: {e}")
            else:
                # Fallback to JSON for Module 1 crowd (backward compatibility)
                global historical_data
                historical_data = update_history(avg_people, now)
            
            # Save audio separately
            if avg_noise is not None and minute_buffers['module1_audio']:
                if USE_DATABASE:
                    try:
                        conn = sqlite3.connect(HISTORY_DB)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO module1_audio (timestamp, noise_db)
                            VALUES (?, ?)
                        ''', (timestamp_str, avg_noise))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"[ERROR] Failed to save Module 1 audio data: {e}")
            
            minute_buffers['module1_crowd'] = []
            minute_buffers['module1_audio'] = []
        
        # Module 2: Environment
        if minute_buffers['module2_env']:
            entries = minute_buffers['module2_env']
            avg_temp = mean([e.get('temperature_c', 0) for e in entries if e.get('temperature_c') is not None]) if any(e.get('temperature_c') for e in entries) else None
            avg_humidity = mean([e.get('humidity_percent', 0) for e in entries if e.get('humidity_percent') is not None]) if any(e.get('humidity_percent') for e in entries) else None
            avg_pressure = mean([e.get('pressure_hpa', 0) for e in entries if e.get('pressure_hpa') is not None]) if any(e.get('pressure_hpa') for e in entries) else None
            avg_uv = mean([e.get('uv_index', 0) for e in entries if e.get('uv_index') is not None]) if any(e.get('uv_index') for e in entries) else None
            avg_comfort = mean([e.get('comfort_score', 0) for e in entries if e.get('comfort_score') is not None]) if any(e.get('comfort_score') for e in entries) else None
            # VOC level: use most common value
            voc_levels = [e.get('voc_level') for e in entries if e.get('voc_level')]
            most_common_voc = max(set(voc_levels), key=voc_levels.count) if voc_levels else None
            
            if USE_DATABASE:
                try:
                    conn = sqlite3.connect(HISTORY_DB)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO module2_environment 
                        (timestamp, temperature_c, humidity_percent, pressure_hpa, uv_index, voc_level, comfort_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (timestamp_str, avg_temp, avg_humidity, avg_pressure, avg_uv, most_common_voc, avg_comfort))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[ERROR] Failed to save Module 2 environment data: {e}")
            
            minute_buffers['module2_env'] = []
        
        # Module 3: Feedback (save immediately, not averaged)
        # This is handled separately in handle_feedback_data

def add_to_buffer(buffer_name, data):
    """Add data point to minute buffer"""
    with buffer_lock:
        if buffer_name in minute_buffers:
            minute_buffers[buffer_name].append(data)

def start_minute_averaging_thread():
    """Start background thread to save minute averages"""
    def averaging_loop():
        while True:
            time.sleep(60)  # Wait 1 minute
            save_minute_averages()
    
    thread = threading.Thread(target=averaging_loop, daemon=True)
    thread.start()
    print("[INFO] Minute-based averaging thread started")

def get_history_from_db(module, start_date=None, end_date=None, limit=1000):
    """Query historical data from database
    
    Args:
        module: 'module1_crowd', 'module1_audio', 'module2_environment', or 'module3_feedback'
        start_date: datetime object or ISO string (optional)
        end_date: datetime object or ISO string (optional)
        limit: maximum number of records to return
    
    Returns:
        List of dictionaries with historical data
    """
    if not USE_DATABASE:
        return []
    
    try:
        conn = sqlite3.connect(HISTORY_DB)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Convert dates to ISO strings if needed
        if start_date and isinstance(start_date, datetime):
            start_date = start_date.isoformat()
        if end_date and isinstance(end_date, datetime):
            end_date = end_date.isoformat()
        
        # Build query
        query = f"SELECT * FROM {module}"
        params = []
        conditions = []
        
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        result = [dict(row) for row in rows]
        
        conn.close()
        return result
    except Exception as e:
        print(f"[ERROR] Failed to query database: {e}")
        return []
>>>>>>> 5cbae18 (Add history system implementation)

# Data storage files
CROWD_DATA_FILE = os.path.join(DATA_DIR, 'crowd_history.json')
ENVIRONMENT_DATA_FILE = os.path.join(DATA_DIR, 'environment_history.json')
FEEDBACK_DATA_FILE = os.path.join(DATA_DIR, 'feedback_history.json')
MODULE_STATES_FILE = os.path.join(DATA_DIR, 'module_states.json')
CONNECTION_HISTORY_FILE = os.path.join(DATA_DIR, 'connection_history.json')

# Legacy history file (for migration)
LEGACY_HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

def load_json_file(filepath, default_value):
    """Load JSON data from file, return default if file doesn't exist or error"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARNING] Could not load {filepath}: {e}")
        import traceback
        traceback.print_exc()
    return default_value

def save_json_file(filepath, data):
    """Save JSON data to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARNING] Could not save {filepath}: {e}")
        import traceback
        traceback.print_exc()

def load_crowd_history():
    """Load all historical crowd data"""
    data = load_json_file(CROWD_DATA_FILE, {'entries': []})
    
    # Migrate from legacy history.json if it exists
    if os.path.exists(LEGACY_HISTORY_FILE) and len(data.get('entries', [])) == 0:
        print("[INFO] Migrating legacy history.json to new format")
        try:
            legacy_data = load_json_file(LEGACY_HISTORY_FILE, {})
            if 'entries' in legacy_data:
                data['entries'] = legacy_data['entries']
                save_json_file(CROWD_DATA_FILE, data)
                print(f"[INFO] Migrated {len(data['entries'])} crowd entries from legacy file")
            elif 'hourly' in legacy_data or 'weekly' in legacy_data:
                # Convert old format
                entries = []
                if 'hourly' in legacy_data:
                    for date_str, hours in legacy_data['hourly'].items():
                        for hour_str, occupancy in hours.items():
                            hour = int(hour_str)
                            people_count = int(occupancy * 10)
                            timestamp_str = f"{date_str}T{hour:02d}:00:00"
                            entries.append({
                                'people_count': people_count,
                                'timestamp': timestamp_str
                            })
                if 'weekly' in legacy_data:
                    for hour_str, days in legacy_data['weekly'].items():
                        hour = int(hour_str)
                        for day_name, occupancies in days.items():
                            for occupancy in occupancies:
                                today = datetime.now()
                                days_offset = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].index(day_name)
                                base_date = today - timedelta(days=(today.weekday() + 7 - days_offset) % 7)
                                date_str = base_date.strftime('%Y-%m-%d')
                                people_count = int(occupancy * 10)
                                timestamp_str = f"{date_str}T{hour:02d}:00:00"
                                entries.append({
                                    'people_count': people_count,
                                    'timestamp': timestamp_str
                                })
                data['entries'] = entries
                save_json_file(CROWD_DATA_FILE, data)
                print(f"[INFO] Migrated {len(entries)} crowd entries from legacy format")
        except Exception as e:
            print(f"[WARNING] Error migrating legacy history: {e}")
    
    return data

def save_crowd_history(data):
    """Save all historical crowd data (keeps ALL records, no time limit)"""
    # Sort by timestamp
    if 'entries' in data:
        data['entries'].sort(key=lambda x: x.get('timestamp', ''))
    save_json_file(CROWD_DATA_FILE, data)

def load_environment_history():
    """Load all historical environment data"""
    return load_json_file(ENVIRONMENT_DATA_FILE, {'entries': []})

def save_environment_history(data):
    """Save all historical environment data (keeps ALL records)"""
    # Sort by timestamp
    if 'entries' in data:
        data['entries'].sort(key=lambda x: x.get('timestamp', ''))
    save_json_file(ENVIRONMENT_DATA_FILE, data)

def load_feedback_history():
    """Load all historical feedback data"""
    return load_json_file(FEEDBACK_DATA_FILE, {'entries': []})

def save_feedback_history(data):
    """Save all historical feedback data (keeps ALL records)"""
    # Sort by timestamp
    if 'entries' in data:
        data['entries'].sort(key=lambda x: x.get('timestamp', ''))
    save_json_file(FEEDBACK_DATA_FILE, data)

def load_module_states():
    """Load module states"""
    return load_json_file(MODULE_STATES_FILE, {
        'module3_state': {
            'last_rating_timestamp': None,
            'latest_rating': None,
            'kiosk_active': False
        }
    })

def save_module_states(data):
    """Save module states"""
    save_json_file(MODULE_STATES_FILE, data)

def load_connection_history():
    """Load connection history"""
    return load_json_file(CONNECTION_HISTORY_FILE, {'connections': []})

def save_connection_history(data):
    """Save connection history"""
    # Keep last 1000 connections to prevent file from growing too large
    if 'connections' in data and len(data['connections']) > 1000:
        data['connections'] = data['connections'][-1000:]
    save_json_file(CONNECTION_HISTORY_FILE, data)

def add_crowd_entry(people_count, timestamp=None, full_data=None):
    """Add a new crowd data entry to history"""
    if timestamp is None:
        timestamp = datetime.now()
    
    history = load_crowd_history()
    if 'entries' not in history:
        history['entries'] = []
    
    timestamp_str = timestamp.isoformat()
    
    # Check if we should add this reading (avoid duplicates from rapid polling)
    # Only add if people_count changed by at least 1, or if last entry is more than 5 minutes old
    should_add = True
    if len(history['entries']) > 0:
        last_entry = history['entries'][-1]
        last_timestamp = datetime.fromisoformat(last_entry.get('timestamp', ''))
        time_diff = (timestamp - last_timestamp).total_seconds()
        people_diff = abs(last_entry.get('people_count', 0) - people_count)
        
        # Add if significant change (>1 person) or if enough time has passed (>5 minutes)
        should_add = people_diff >= 1 or time_diff >= 300
    
    if should_add:
        entry = {
            'people_count': int(people_count),
            'timestamp': timestamp_str
        }
        # Include full data if provided
        if full_data:
            entry['full_data'] = full_data
        history['entries'].append(entry)
        save_crowd_history(history)
    
    return history

def add_environment_entry(env_data, timestamp=None):
    """Add a new environment data entry to history"""
    if timestamp is None:
        timestamp = datetime.now()
    
    history = load_environment_history()
    if 'entries' not in history:
        history['entries'] = []
    
    timestamp_str = timestamp.isoformat()
    
    # Always add environment data (less frequent updates)
    entry = {
        'timestamp': timestamp_str,
        'data': env_data
    }
    history['entries'].append(entry)
    save_environment_history(history)
    
    return history

def add_feedback_entry(feedback_data, timestamp=None):
    """Add a new feedback data entry to history"""
    if timestamp is None:
        timestamp = datetime.now()
    
    history = load_feedback_history()
    if 'entries' not in history:
        history['entries'] = []
    
    timestamp_str = timestamp.isoformat()
    
    # Always add feedback data (user interactions are important)
    entry = {
        'timestamp': timestamp_str,
        'data': feedback_data
    }
    history['entries'].append(entry)
    save_feedback_history(history)
    
    return history

def add_connection_event(module_id, module_type, event_type, timestamp=None):
    """Add a connection/disconnection event to history"""
    if timestamp is None:
        timestamp = datetime.now()
    
    history = load_connection_history()
    if 'connections' not in history:
        history['connections'] = []
    
    entry = {
        'module_id': module_id,
        'module_type': module_type,
        'event': event_type,  # 'connected' or 'disconnected'
        'timestamp': timestamp.isoformat()
    }
    history['connections'].append(entry)
    save_connection_history(history)
    
    return history

# Legacy function for backward compatibility
def load_history():
    """Legacy function - loads crowd history for backward compatibility"""
    return load_crowd_history()

def update_history(people_count, timestamp=None):
    """Legacy function - updates crowd history for backward compatibility"""
    return add_crowd_entry(people_count, timestamp)

# --- Historical Data Retrieval Functions ---
def get_latest_crowd_data():
    """Get the most recent crowd data from history if current_data is None"""
    if current_data.get('crowd'):
        return current_data['crowd']
    
    # Fallback to historical data
    history = load_crowd_history()
    if 'entries' in history and len(history['entries']) > 0:
        # Get most recent entry
        latest_entry = history['entries'][-1]
        # Reconstruct data structure
        return {
            'module_id': 'historical',
            'module_type': 'crowd_detection',
            'timestamp': latest_entry.get('timestamp'),
            'data': {
                'people_count': latest_entry.get('people_count', 0),
                'crowd_level': 'empty' if latest_entry.get('people_count', 0) == 0 else 'normal',
                'confidence': 0.85,
                'source': 'historical'
            }
        }
    return None

def get_latest_environment_data():
    """Get the most recent environment data from history if current_data is None"""
    if current_data.get('environment'):
        return current_data['environment']
    
    # Fallback to historical data
    history = load_environment_history()
    if 'entries' in history and len(history['entries']) > 0:
        # Get most recent entry
        latest_entry = history['entries'][-1]
        # Reconstruct data structure
        return {
            'module_id': 'historical',
            'module_type': 'environment',
            'timestamp': latest_entry.get('timestamp'),
            'data': latest_entry.get('data', {})
        }
    return None

def get_recent_feedback_data(count=50):
    """Get recent feedback data, combining current_data and history"""
    feedback_list = current_data.get('feedback', []).copy()
    
    # If we have less than requested, get from history
    if len(feedback_list) < count:
        history = load_feedback_history()
        if 'entries' in history:
            # Get recent entries from history
            recent_from_history = history['entries'][-count:]
            for entry in recent_from_history:
                # Check if not already in current_data
                entry_data = entry.get('data', {})
                if entry_data not in [f for f in feedback_list]:
                    feedback_list.append(entry_data)
            # Sort by timestamp and take most recent
            feedback_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return feedback_list[:count]
    
    return feedback_list

def update_module_status(module_type, module_id, is_online=True):
    """Update module online/offline status"""
    if module_type not in module_status:
        module_status[module_type] = {}
    
    if module_id not in module_status[module_type]:
        module_status[module_type][module_id] = {}
    
    module_status[module_type][module_id]['online'] = is_online
    module_status[module_type][module_id]['last_seen'] = datetime.now().isoformat()
    
    return module_status[module_type][module_id]

def get_module_status_summary():
    """Get summary of all module statuses"""
    summary = {}
    for module_type, modules in module_status.items():
        summary[module_type] = {
            'total': len(modules),
            'online': sum(1 for m in modules.values() if m.get('online', False)),
            'offline': sum(1 for m in modules.values() if not m.get('online', False)),
            'modules': modules
        }
    return summary

def get_today_hourly_pattern(history, current_hour, current_people_count, capacity=10):
    """Calculate hourly pattern for today from raw history entries - server-side calculation"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    today_hourly = []
    
    # Get all entries for today
    today_entries = []
    if 'entries' in history:
        for entry in history['entries']:
            entry_timestamp = entry.get('timestamp', '')
            if entry_timestamp.startswith(date_str):
                try:
                    entry_dt = datetime.fromisoformat(entry_timestamp)
                    today_entries.append({
                        'hour': entry_dt.hour,
                        'people_count': entry.get('people_count', 0)
                    })
                except:
                    continue
    
    # Calculate average people count per hour for today
    for hour in range(8, 22):  # 8 AM to 10 PM
        if hour < current_hour:
            # Past hours: calculate average from entries in this hour
            hour_entries = [e for e in today_entries if e['hour'] == hour]
            if hour_entries:
                avg_people = sum(e['people_count'] for e in hour_entries) / len(hour_entries)
                occupancy = min(1.0, max(0.0, avg_people / capacity))
                today_hourly.append({'hour': hour, 'occupancy': occupancy, 'people_count': int(avg_people)})
            # If no data, skip this hour
        elif hour == current_hour:
            # Current hour: use actual current people count
            occupancy = min(1.0, max(0.0, current_people_count / capacity))
            today_hourly.append({'hour': hour, 'occupancy': occupancy, 'people_count': current_people_count})
        else:
            # Future hours: skip (don't show projections)
            pass
    
    return today_hourly

def get_weekly_pattern(history, current_hour, current_people_count, capacity=10):
    """Calculate weekly pattern for same time across different days from raw history - server-side calculation"""
    week_same_time = []
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Get all entries for the current hour across all days
    hour_entries_by_day = {day: [] for day in days}
    
    if 'entries' in history:
        for entry in history['entries']:
            entry_timestamp = entry.get('timestamp', '')
            try:
                entry_dt = datetime.fromisoformat(entry_timestamp)
                if entry_dt.hour == current_hour:
                    # Get day name (0=Monday, 6=Sunday)
                    day_index = entry_dt.weekday()
                    day_name = days[day_index]
                    hour_entries_by_day[day_name].append(entry.get('people_count', 0))
            except:
                continue
    
    # Calculate average for each day
    for day in days:
        day_entries = hour_entries_by_day[day]
        if day_entries and len(day_entries) > 0:
            avg_people = sum(day_entries) / len(day_entries)
            occupancy = min(1.0, max(0.0, avg_people / capacity))
            week_same_time.append({
                'day': day, 
                'occupancy': occupancy,
                'people_count': int(avg_people)
            })
        else:
            # No data for this day - add with null/None occupancy so graph skips it
            week_same_time.append({'day': day, 'occupancy': None, 'people_count': None})
    
    return week_same_time

<<<<<<< HEAD
# Initialize all historical data on startup
historical_data = load_crowd_history()
crowd_entry_count = len(historical_data.get('entries', []))

environment_history = load_environment_history()
env_entry_count = len(environment_history.get('entries', []))

feedback_history = load_feedback_history()
feedback_entry_count = len(feedback_history.get('entries', []))

module_states = load_module_states()
connection_history = load_connection_history()
connection_count = len(connection_history.get('connections', []))

# Initialize all historical data on startup
historical_data = load_crowd_history()
crowd_entry_count = len(historical_data.get('entries', []))

environment_history = load_environment_history()
env_entry_count = len(environment_history.get('entries', []))

feedback_history = load_feedback_history()
feedback_entry_count = len(feedback_history.get('entries', []))

module_states = load_module_states()
connection_history = load_connection_history()
connection_count = len(connection_history.get('connections', []))

print(f"[INFO] Historical data loaded:")
print(f"  - Crowd data: {crowd_entry_count} entries")
print(f"  - Environment data: {env_entry_count} entries")
print(f"  - Feedback data: {feedback_entry_count} entries")
print(f"  - Connection history: {connection_count} events")

# Initialize history on startup
if USE_DATABASE:
    init_database()
else:
    historical_data = load_history()
    entry_count = len(historical_data.get('entries', []))
    print(f"[INFO] Historical data loaded: {entry_count} entries tracked")

# Start minute-based averaging thread
start_minute_averaging_thread()

# --- Data Storage ---
connected_modules = {
    'crowd_detection': [],
    'environment': [],
    'feedback': [],
    'display': []  # Module 5 display clients
}

# Track which socket IDs are display modules
display_module_sockets = {}  # {socket_id: module_id}

# Module status tracking (online/offline, last seen)
module_status = {
    'crowd_detection': {},  # {module_id: {'online': bool, 'last_seen': timestamp}}
    'environment': {},
    'feedback': {},
    'display': {}
}

# Track which socket IDs are feedback modules (Module 3)
feedback_module_sockets = {}  # {socket_id: module_id}

# Current data from each module type
current_data = {
    'crowd': None,
    'environment': None,
    'feedback': []
}

# Module 3 specific tracking (loaded from persistent storage)
module3_state = module_states.get('module3_state', {
    'last_rating_timestamp': None,  # ISO timestamp of last rating interaction
    'latest_rating': None,  # Latest rating value (1-5)
    'kiosk_active': False  # Whether kiosk is currently in use
})

def save_module3_state():
    """Save module3 state to persistent storage"""
    module_states['module3_state'] = module3_state
    save_module_states(module_states)

# --- Mock Mode State ---
mock_state = {
    'active': False,
    'scenario': 'normal',  # 'empty', 'light', 'normal', 'busy', 'full'
    'update_interval': 30,  # seconds
    'threads': []
}

# ===== MOCK DATA GENERATORS =====

def generate_mock_crowd_data(scenario='normal'):
    """Generate realistic mock crowd detection data"""
    scenarios = {
        'empty': {'people': (0, 1), 'noise': (30, 45), 'motion': 0.1, 'proximity': 0.1},
        'light': {'people': (1, 3), 'noise': (45, 60), 'motion': 0.4, 'proximity': 0.3},
        'normal': {'people': (4, 6), 'noise': (55, 70), 'motion': 0.7, 'proximity': 0.6},
        'busy': {'people': (6, 8), 'noise': (65, 80), 'motion': 0.9, 'proximity': 0.8},
        'full': {'people': (8, 10), 'noise': (75, 90), 'motion': 1.0, 'proximity': 1.0}
    }
    
    config = scenarios.get(scenario, scenarios['normal'])
    people_count = random.randint(*config['people'])
    
    # Determine crowd level based on people count
    if people_count == 0:
        level = 'empty'
    elif people_count <= 2:
        level = 'light'
    elif people_count <= 5:
        level = 'normal'
    elif people_count <= 7:
        level = 'busy'
    else:
        level = 'full'
    
    return {
        'module_id': 'mock_module1',
        'module_type': 'crowd_detection',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'people_count': people_count,
            'crowd_level': level,
            'confidence': round(random.uniform(0.85, 0.98), 2),
            'noise_db': random.randint(*config['noise']),
            'motion_detected': random.random() < config['motion'],
            'proximity_triggered': random.random() < config['proximity']
        }
    }

def generate_mock_environment_data(scenario='normal'):
    """Generate realistic mock environment sensor data"""
    # Time-based variations (hotter during day, cooler at night)
    current_hour = datetime.now().hour
    is_daytime = 8 <= current_hour <= 18
    
    scenarios = {
        'empty': {'temp': (22, 26), 'humidity': (40, 55), 'uv': (2, 5), 'comfort': (4.0, 5.0)},
        'light': {'temp': (24, 28), 'humidity': (45, 60), 'uv': (4, 6), 'comfort': (3.5, 4.5)},
        'normal': {'temp': (26, 30), 'humidity': (50, 65), 'uv': (5, 8), 'comfort': (3.0, 4.0)},
        'busy': {'temp': (28, 32), 'humidity': (55, 70), 'uv': (7, 10), 'comfort': (2.5, 3.5)},
        'full': {'temp': (30, 35), 'humidity': (60, 75), 'uv': (8, 11), 'comfort': (2.0, 3.0)}
    }
    
    config = scenarios.get(scenario, scenarios['normal'])
    
    # Adjust temperature based on time of day
    temp_range = config['temp']
    if not is_daytime:
        temp_range = (temp_range[0] - 5, temp_range[1] - 5)
    
    temp = random.randint(*temp_range)
    humidity = random.randint(*config['humidity'])
    uv = random.randint(*config['uv']) if is_daytime else random.randint(0, 2)
    comfort = round(random.uniform(*config['comfort']), 1)
    
    # Determine VOC level
    if temp > 32 or humidity > 70:
        voc_level = 'moderate'
    elif temp > 35 or humidity > 80:
        voc_level = 'poor'
    else:
        voc_level = 'good'
    
    # Generate warnings
    warnings = []
    if uv > 7:
        warnings.append('High UV - Use sunscreen')
    if temp > 32:
        warnings.append('High temperature - Stay hydrated')
    if humidity > 70:
        warnings.append('High humidity')
    
    return {
        'module_id': 'mock_module2',
        'module_type': 'environment',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'temperature_c': temp,
            'humidity_percent': humidity,
            'uv_index': uv,
            'voc_level': voc_level,
            'voc_reading': random.randint(50, 500) if voc_level != 'good' else random.randint(0, 100),
            'comfort_score': comfort,
            'warnings': warnings
        }
    }

def generate_mock_feedback_data(scenario='normal'):
    """Generate realistic mock feedback data"""
    scenarios = {
        'empty': {'rating': (4, 5), 'issues': ['None', 'Too quiet']},
        'light': {'rating': (4, 5), 'issues': ['Clean', 'Well maintained']},
        'normal': {'rating': (3, 4), 'issues': ['Slightly crowded', 'Good atmosphere']},
        'busy': {'rating': (2, 4), 'issues': ['Very crowded', 'Waiting time', 'Noisy']},
        'full': {'rating': (2, 3), 'issues': ['Overcrowded', 'Long wait', 'Need maintenance']}
    }
    
    config = scenarios.get(scenario, scenarios['normal'])
    
    # Alternate between rating and text feedback
    report_type = random.choice(['rating', 'text'])
    
    if report_type == 'rating':
        questions = [
            'How would you rate this facility?',
            'Overall satisfaction?',
            'Would you recommend this court?'
        ]
        return {
            'module_id': 'mock_module3',
            'module_type': 'feedback',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'rating',
                'question_text': random.choice(questions),
                'rating': random.randint(*config['rating']),
                'rating_scale': 5
            }
        }
    else:
        questions = [
            'Any issues to report?',
            'What can we improve?',
            'Maintenance needed?'
        ]
        categories = ['cleanliness', 'maintenance', 'crowding', 'equipment', 'other']
        return {
            'module_id': 'mock_module3',
            'module_type': 'feedback',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'text',
                'question_text': random.choice(questions),
                'text_response': random.choice(config['issues']),
                'issue_category': random.choice(categories)
            }
        }

def mock_data_loop():
    """Background thread that generates mock data periodically"""
    print(f"[{datetime.now()}] Mock data generator started")
    
    while mock_state['active']:
        try:
            scenario = mock_state['scenario']
            
            # Generate mock data for all three modules
            crowd_data = generate_mock_crowd_data(scenario)
            env_data = generate_mock_environment_data(scenario)
            
            # Process mock data through the actual handlers (as if real hardware sent them)
            # This ensures the server processes them through the normal handlers
            # which will automatically generate and send Module 5 data
            handle_crowd_data(crowd_data)
            handle_environment_data(env_data)
            
            # Generate feedback less frequently (30% chance)
            if random.random() < 0.3:
                feedback_data = generate_mock_feedback_data(scenario)
                handle_feedback_data(feedback_data)
            
            print(f"[{datetime.now()}] Mock data sent (scenario: {scenario})")
            
            # Wait for next update
            time.sleep(mock_state['update_interval'])
            
        except Exception as e:
            print(f"[{datetime.now()}] Error in mock data loop: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print(f"[{datetime.now()}] Mock data generator stopped")

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'guest':
            return redirect(url_for('guest_dashboard'))
        else:
            return redirect(url_for('personnel_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Auto-detect role by checking credentials in both user dictionaries
        role = None
        if username in USERS['personnel'] and USERS['personnel'][username] == password:
            role = 'personnel'
        elif username in USERS['guest'] and USERS['guest'][username] == password:
            role = 'guest'
        
        # Validate credentials
        if role:
            session['user_id'] = username
            session['role'] = role
            session['username'] = username
            return jsonify({
                'success': True,
                'role': role,
                'username': username
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
    
    # GET request - show login page
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/guest_dashboard')
@login_required(role='guest')
def guest_dashboard():
    return render_template('guest_dashboard.html', username=session.get('username', 'Guest'))

@app.route('/personnel_dashboard')
@login_required(role='personnel')
def personnel_dashboard():
    return render_template('personnel_dashboard.html', username=session.get('username', 'Personnel'))

@app.route('/module5')
def module5_test():
    return render_template('module5.html')

@app.route('/module3')
def module1_test():
    return render_template('module3.html')

@app.route('/debug')
def debug_page():
    return render_template('debug.html')

@app.route('/api/analyze_image', methods=['POST'])
def analyze_image():
    """Analyze uploaded image using Claude AI for people counting"""
    try:
        if not anthropic_client:
            return jsonify({'error': 'AI service not available. ANTHROPIC_API_KEY not configured.'}), 503
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read and encode image (using standard_b64encode as per documentation)
        image_data = file.read()
        image_base64 = base64.standard_b64encode(image_data).decode('utf-8')
        
        # Determine content type
        content_type = file.content_type or 'image/jpeg'
        
        # Validate file size (max 16MB as per documentation)
        max_size = 16 * 1024 * 1024  # 16MB
        if len(image_data) > max_size:
            return jsonify({'error': f'File too large. Maximum size is {max_size / (1024*1024):.0f}MB'}), 400
        
        print(f"[{datetime.now()}] Analyzing image with AI (size: {len(image_data)} bytes)")
        
        # Send to Claude API
        message = anthropic_client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1000,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': content_type,
                            'data': image_base64,
                        },
                    },
                    {
                        'type': 'text',
                        'text': '''Count the number of people visible in this image, regardless of the scene type (basketball court, meeting room, study space, etc.). 
                        Always return a people count even if the scene is not a basketball court.
                        Analyze the scene and return ONLY valid JSON in this exact format:
                        {
                            "count": <number>,
                            "details": "<brief description of scene and people>",
                            "crowd_level": "<empty|light|normal|busy|full>",
                            "confidence": <0.0-1.0>
                        }
                        Do not include any markdown formatting or code blocks. Always provide a count value, even if the scene type doesn't match expectations.'''
                    }
                ],
            }],
        )
        
        # Parse response
        response_text = message.content[0].text.strip()
        # Remove markdown code blocks if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Check if response contains error about scene type but try to extract count anyway
        scene_type_warning = False
        if 'not a basketball court' in response_text.lower() or 'basketball court' in response_text.lower():
            scene_type_warning = True
            print(f"[{datetime.now()}] Warning: Scene type mismatch detected, but attempting to extract people count anyway")
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response (handle cases where Claude adds text before/after JSON)
            import re
            # Try to find JSON object in response (more robust pattern)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # If still fails, try to extract just the count number
                    count_match = re.search(r'"count"\s*:\s*(\d+)', response_text)
                    if count_match:
                        people_count = int(count_match.group(1))
                        result = {
                            'count': people_count,
                            'details': response_text[:100] if len(response_text) > 100 else response_text,
                            'crowd_level': 'normal',
                            'confidence': 0.7
                        }
                        print(f"[{datetime.now()}] Extracted people count from text response: {people_count}")
                    else:
                        raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")
                else:
                    # Last resort: try to extract just the count number from various patterns
                    count_match = re.search(r'"count"\s*:\s*(\d+)', response_text)
                    if not count_match:
                        # Try other patterns: "count": 5, count: 5, "people": 5, etc.
                        count_match = re.search(r'(?:count|people|people_count|number_of_people)"?\s*:?\s*(\d+)', response_text, re.IGNORECASE)
                    if not count_match:
                        # Try to find any number that might be a count (look for numbers near "people" or "person")
                        count_match = re.search(r'(?:people|person|individuals?)\D+(\d+)', response_text, re.IGNORECASE)
                    if count_match:
                        people_count = int(count_match.group(1))
                        result = {
                            'count': people_count,
                            'details': response_text[:200] if len(response_text) > 200 else response_text,
                            'crowd_level': 'normal' if people_count > 0 else 'empty',
                            'confidence': 0.6  # Lower confidence since we had to extract from text
                        }
                        print(f"[{datetime.now()}] Extracted people count from text response: {people_count}")
                    else:
                        # Final fallback: return 0 with warning
                        print(f"[{datetime.now()}] WARNING: Could not extract people count from response: {response_text[:300]}")
                        result = {
                            'count': 0,
                            'details': f"Could not parse response. Original: {response_text[:200]}",
                            'crowd_level': 'empty',
                            'confidence': 0.0
                        }
        
        print(f"[{datetime.now()}] AI Analysis result: {result}")
        
        # Extract people count and confidence from AI result
        people_count = result.get('count', 0)
        confidence = result.get('confidence', 0.85)
        crowd_level = result.get('crowd_level', 'empty')
        
        # Map crowd_level to standard values if needed
        if isinstance(crowd_level, str):
            crowd_level = crowd_level.lower()
            if crowd_level not in ['empty', 'light', 'normal', 'busy', 'full']:
                # Map to closest standard level
                if people_count == 0:
                    crowd_level = 'empty'
                elif people_count <= 2:
                    crowd_level = 'light'
                elif people_count <= 5:
                    crowd_level = 'normal'
                elif people_count <= 7:
                    crowd_level = 'busy'
                else:
                    crowd_level = 'full'
        
        # Create crowd data structure for Module 1
        crowd_data = {
            'module_id': 'ai_image_analysis',
            'module_type': 'crowd_detection',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'people_count': people_count,
                'crowd_level': crowd_level,
                'confidence': confidence,
                'source': 'ai_image_analysis'
            },
            '_ai_analysis': True,  # Flag to mark this as AI analysis data
            '_ai_timestamp': datetime.now().isoformat()  # Store timestamp for comparison
        }
        
        # Update current_data with AI analysis results
        current_data['crowd'] = crowd_data
        
        # Save to persistent storage with full historical records
        global historical_data
        historical_data = add_crowd_entry(people_count, datetime.now(), full_data=crowd_data)
        
        # Get historical patterns for graphs (calculated server-side from raw data)
        current_hour = datetime.now().hour
        capacity = 10  # Default capacity
        today_hourly = get_today_hourly_pattern(historical_data, current_hour, people_count, capacity)
        week_same_time = get_weekly_pattern(historical_data, current_hour, people_count, capacity)
        
        # Generate complete Module 5 data for preview (merge with existing data if available)
        # Use generate_module5_from_modules to ensure complete data structure
        # Use historical data as fallback if current data is missing
        env_data_for_module5 = current_data.get('environment') or get_latest_environment_data()
        feedback_data_for_module5 = current_data.get('feedback') if current_data.get('feedback') else get_recent_feedback_data(10)
        
        complete_module5_data = generate_module5_from_modules(
            court_id='basketball_a',
            crowd_data=crowd_data,  # Use the AI analysis crowd data
            env_data=env_data_for_module5,
            feedback_data=feedback_data_for_module5 if feedback_data_for_module5 else None
        )
        
        # Override the current section with AI analysis data to ensure it's displayed
        complete_module5_data['current'].update({
            'people_count': people_count,
            'crowd_level': crowd_level,
            'confidence': confidence,
            'last_update': 'Just now',
            'source': 'ai_image_analysis'
        })
        
        # Emit complete Module 5 update (includes all sections for preview)
        socketio.emit('DisplayUpdate', complete_module5_data)
        
        # Also emit to dashboard for preview
        socketio.emit('crowd_update', crowd_data)
        
        # Calculate occupancy for logging
        occupancy = complete_module5_data.get('current', {}).get('occupancy', min(1.0, people_count / 10.0))
        print(f"[{datetime.now()}] Sent AI analysis to Module 5: {people_count} people, {confidence:.2%} confidence, occupancy: {occupancy:.1%}")
        
        # Emit result via SocketIO for real-time dashboard update
        socketio.emit('ai_analysis_result', {
            'timestamp': datetime.now().isoformat(),
            'result': result,
            'image_size': len(image_data),
            'module5_sent': True
        })
        
        return jsonify({
            'success': True,
            'result': result,
            'people_count': people_count,
            'confidence': confidence,
            'crowd_level': crowd_level,
            'module5_sent': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"[{datetime.now()}] Error analyzing image: {error_msg}")
        return jsonify({'error': error_msg}), 500

@app.route('/api/current_data')
def get_current_data():
    """API endpoint to get current data state for polling - uses historical data as fallback when modules offline"""
    # Get data with historical fallback
    crowd_data = get_latest_crowd_data()
    env_data = get_latest_environment_data()
    feedback_data = get_recent_feedback_data(50)
    
    # Always generate Module 5 data if we have any data (current or historical)
    module5_data = None
    if crowd_data or env_data:
        module5_data = generate_module5_from_modules(
            court_id='basketball_a',
            crowd_data=crowd_data,
            env_data=env_data,
            feedback_data=feedback_data if feedback_data else None
        )
    
    # Get module status
    module_status_summary = get_module_status_summary()
    
    return jsonify({
        'crowd': crowd_data,
        'environment': env_data,
        'feedback': feedback_data[-1] if feedback_data else None,
        'feedback_recent': feedback_data[:10] if feedback_data else [],
        'module5': module5_data,
        'module_status': module_status_summary,
        'timestamp': datetime.now().isoformat()
    })

# --- Historical Data API Endpoints ---
@app.route('/api/history/crowd')
def get_crowd_history():
    """Get historical crowd data with optional filters"""
    try:
        days = int(request.args.get('days', 7))  # Default: last 7 days
        limit = int(request.args.get('limit', 1000))  # Default: max 1000 entries
        
        history = load_crowd_history()
        entries = history.get('entries', [])
        
        # Filter by date
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_str]
        
        # Limit results
        entries = entries[-limit:] if len(entries) > limit else entries
        
        return jsonify({
            'entries': entries,
            'count': len(entries),
            'days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/environment')
def get_environment_history():
    """Get historical environment data with optional filters"""
    try:
        days = int(request.args.get('days', 7))  # Default: last 7 days
        limit = int(request.args.get('limit', 1000))  # Default: max 1000 entries
        
        history = load_environment_history()
        entries = history.get('entries', [])
        
        # Filter by date
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_str]
        
        # Limit results
        entries = entries[-limit:] if len(entries) > limit else entries
        
        return jsonify({
            'entries': entries,
            'count': len(entries),
            'days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/feedback')
def get_feedback_history():
    """Get historical feedback data with optional filters"""
    try:
        days = int(request.args.get('days', 30))  # Default: last 30 days
        limit = int(request.args.get('limit', 500))  # Default: max 500 entries
        
        history = load_feedback_history()
        entries = history.get('entries', [])
        
        # Filter by date
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_str]
        
        # Limit results
        entries = entries[-limit:] if len(entries) > limit else entries
        
        return jsonify({
            'entries': entries,
            'count': len(entries),
            'days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Analytics API Endpoints ---
@app.route('/api/analytics/crowd')
def get_crowd_analytics():
    """Get crowd analytics (statistics, trends, hourly patterns)"""
    try:
        days = int(request.args.get('days', 7))
        
        history = load_crowd_history()
        entries = history.get('entries', [])
        
        # Filter by date
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_str]
        
        if not entries:
            return jsonify({
                'statistics': {},
                'hourly_average': [],
                'daily_average': [],
                'trends': {}
            })
        
        # Calculate statistics
        people_counts = [e.get('people_count', 0) for e in entries]
        stats = {
            'total_readings': len(entries),
            'average': round(sum(people_counts) / len(people_counts), 2) if people_counts else 0,
            'min': min(people_counts) if people_counts else 0,
            'max': max(people_counts) if people_counts else 0,
            'median': sorted(people_counts)[len(people_counts) // 2] if people_counts else 0
        }
        
        # Hourly averages
        hourly_data = defaultdict(list)
        for entry in entries:
            try:
                entry_dt = datetime.fromisoformat(entry.get('timestamp', ''))
                hour = entry_dt.hour
                hourly_data[hour].append(entry.get('people_count', 0))
            except:
                continue
        
        hourly_average = []
        for hour in range(24):
            if hour in hourly_data:
                avg = sum(hourly_data[hour]) / len(hourly_data[hour])
                hourly_average.append({'hour': hour, 'average': round(avg, 2), 'count': len(hourly_data[hour])})
            else:
                hourly_average.append({'hour': hour, 'average': 0, 'count': 0})
        
        # Daily averages
        daily_data = defaultdict(list)
        for entry in entries:
            try:
                entry_dt = datetime.fromisoformat(entry.get('timestamp', ''))
                date_str = entry_dt.strftime('%Y-%m-%d')
                daily_data[date_str].append(entry.get('people_count', 0))
            except:
                continue
        
        daily_average = []
        for date_str in sorted(daily_data.keys()):
            avg = sum(daily_data[date_str]) / len(daily_data[date_str])
            daily_average.append({'date': date_str, 'average': round(avg, 2), 'count': len(daily_data[date_str])})
        
        # Trends (compare last 3 days vs previous 3 days)
        if len(entries) > 10:
            mid_point = len(entries) // 2
            recent = entries[mid_point:]
            previous = entries[:mid_point]
            
            recent_avg = sum(e.get('people_count', 0) for e in recent) / len(recent) if recent else 0
            previous_avg = sum(e.get('people_count', 0) for e in previous) / len(previous) if previous else 0
            
            trend = 'increasing' if recent_avg > previous_avg else 'decreasing' if recent_avg < previous_avg else 'stable'
            change_percent = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        else:
            trend = 'insufficient_data'
            change_percent = 0
        
        return jsonify({
            'statistics': stats,
            'hourly_average': hourly_average,
            'daily_average': daily_average,
            'trends': {
                'direction': trend,
                'change_percent': round(change_percent, 2)
            },
            'days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/environment')
def get_environment_analytics():
    """Get environment analytics (temperature, humidity trends)"""
    try:
        days = int(request.args.get('days', 7))
        
        history = load_environment_history()
        entries = history.get('entries', [])
        
        # Filter by date
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_str]
        
        if not entries:
            return jsonify({
                'temperature': {},
                'humidity': {},
                'comfort_score': {},
                'hourly_average': []
            })
        
        # Extract data
        temps = []
        humidities = []
        comfort_scores = []
        
        for entry in entries:
            data = entry.get('data', {})
            if 'temperature_c' in data:
                temps.append(data['temperature_c'])
            if 'humidity_percent' in data:
                humidities.append(data['humidity_percent'])
            if 'comfort_score' in data:
                comfort_scores.append(data['comfort_score'])
        
        # Calculate statistics
        temp_stats = {
            'average': round(sum(temps) / len(temps), 2) if temps else None,
            'min': min(temps) if temps else None,
            'max': max(temps) if temps else None
        }
        
        humidity_stats = {
            'average': round(sum(humidities) / len(humidities), 2) if humidities else None,
            'min': min(humidities) if humidities else None,
            'max': max(humidities) if humidities else None
        }
        
        comfort_stats = {
            'average': round(sum(comfort_scores) / len(comfort_scores), 2) if comfort_scores else None,
            'min': min(comfort_scores) if comfort_scores else None,
            'max': max(comfort_scores) if comfort_scores else None
        }
        
        # Hourly averages for temperature
        hourly_temp = defaultdict(list)
        for entry in entries:
            try:
                entry_dt = datetime.fromisoformat(entry.get('timestamp', ''))
                hour = entry_dt.hour
                data = entry.get('data', {})
                if 'temperature_c' in data:
                    hourly_temp[hour].append(data['temperature_c'])
            except:
                continue
        
        hourly_average = []
        for hour in range(24):
            if hour in hourly_temp:
                avg = sum(hourly_temp[hour]) / len(hourly_temp[hour])
                hourly_average.append({'hour': hour, 'temperature': round(avg, 2), 'count': len(hourly_temp[hour])})
            else:
                hourly_average.append({'hour': hour, 'temperature': None, 'count': 0})
        
        return jsonify({
            'temperature': temp_stats,
            'humidity': humidity_stats,
            'comfort_score': comfort_stats,
            'hourly_average': hourly_average,
            'days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/feedback')
def get_feedback_analytics():
    """Get feedback analytics (ratings, trends, distribution)"""
    try:
        days = int(request.args.get('days', 30))
        
        history = load_feedback_history()
        entries = history.get('entries', [])
        
        # Filter by date
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            entries = [e for e in entries if e.get('timestamp', '') >= cutoff_str]
        
        # Extract ratings
        ratings = []
        text_feedback = []
        
        for entry in entries:
            data = entry.get('data', {})
            if data.get('report_type') == 'rating' and 'rating' in data:
                ratings.append(data['rating'])
            elif data.get('report_type') == 'text':
                text_feedback.append(data)
        
        # Calculate statistics
        rating_stats = {}
        if ratings:
            rating_stats = {
                'total': len(ratings),
                'average': round(sum(ratings) / len(ratings), 2),
                'min': min(ratings),
                'max': max(ratings),
                'distribution': {i: ratings.count(i) for i in range(1, 6)}
            }
        
        # Text feedback categories
        categories = defaultdict(int)
        for feedback in text_feedback:
            category = feedback.get('issue_category', 'other')
            categories[category] += 1
        
        return jsonify({
            'ratings': rating_stats,
            'text_feedback_count': len(text_feedback),
            'categories': dict(categories),
            'total_feedback': len(entries),
            'days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/module_status')
def get_module_status_api():
    """Get current status of all modules"""
    return jsonify({
        'status': get_module_status_summary(),
        'connected_modules': connected_modules,
        'timestamp': datetime.now().isoformat()
    })

# --- Module Registration ---
@socketio.on('module_register')
def handle_module_register(data):
    """Register a module when it connects"""
    module_id = data.get('module_id', 'unknown')
    module_type = data.get('module_type', 'unknown')
    socket_id = request.sid
    
    if module_type in connected_modules:
        if module_id not in connected_modules[module_type]:
            connected_modules[module_type].append(module_id)
            # Save connection event to history
            add_connection_event(module_id, module_type, 'connected')
        print(f"[{datetime.now()}] Module registered: {module_id} ({module_type})")
        
        # Track display module sockets
        if module_type == 'display':
            display_module_sockets[socket_id] = module_id
        
        # Track feedback module sockets
        if module_type == 'feedback':
            feedback_module_sockets[socket_id] = module_id
        
        # Notify dashboard of new connection
        socketio.emit('module_connected', {
            'module_id': module_id,
            'module_type': module_type,
            'timestamp': datetime.now().isoformat()
        })
        
        # Emit specific event for Module 5 display connections
        if module_type == 'display':
            socketio.emit('module5_display_connected', {
                'module_id': module_id,
                'court_id': data.get('court_id', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'count': len(connected_modules['display'])
            })

# --- MODULE 1: CROWD DETECTION DATA ---
@socketio.on('CrowdDataEvent')
def handle_crowd_data(data):
    """Receive crowd detection data from Module 1"""
    print(f"[{datetime.now()}] Received Crowd Data: {data}")
    current_data['crowd'] = data
    
<<<<<<< HEAD
    # Update module status
    module_id = data.get('module_id', 'unknown')
    update_module_status('crowd_detection', module_id, is_online=True)
    
    # Save to persistent storage with full historical records
    # Add to minute buffer for averaging
    if 'data' in data:
        people_count = data['data'].get('people_count', 0)
        noise_db = data['data'].get('noise_db')
        timestamp = datetime.now()
        
        # Add to crowd buffer (includes both people_count and noise)
        add_to_buffer('module1_crowd', {
            'people_count': people_count,
            'noise_db': noise_db,
            'timestamp': timestamp
        })
        
        # Also add to audio buffer if noise data available
        if noise_db is not None:
            add_to_buffer('module1_audio', {
                'noise_db': noise_db,
                'timestamp': timestamp
            })
        
        # Legacy JSON support (for backward compatibility)
        if not USE_DATABASE:
            occupancy = min(1.0, people_count / 10.0)
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
<<<<<<< HEAD
        else:
            timestamp = datetime.now()
        # Save to persistent storage with full data
        global historical_data
        historical_data = add_crowd_entry(people_count, timestamp, full_data=data)
        # Also add to minute buffer for averaging
        add_to_buffer('module1_crowd', {
            'people_count': people_count,
            'noise_db': data.get('data', {}).get('noise_db'),
            'timestamp': timestamp.isoformat()
        })
    
    socketio.emit('crowd_update', data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data (with historical fallback)
    court_id = data.get('court_id', 'basketball_a')
    # Use historical data as fallback if current data is missing
    env_data_for_module5 = current_data.get('environment') or get_latest_environment_data()
    feedback_data_for_module5 = current_data.get('feedback') if current_data.get('feedback') else get_recent_feedback_data(10)
    
    module5_data = generate_module5_from_modules(
        court_id=court_id,
        crowd_data=data,
        env_data=env_data_for_module5,
        feedback_data=feedback_data_for_module5 if feedback_data_for_module5 else None
    )
    
    # Emit DisplayUpdate to all clients (including preview and Module 5 displays)
    connected_display_count = len(connected_modules['display'])
    print(f"[{datetime.now()}] Broadcasting DisplayUpdate from Module 1 to all clients ({connected_display_count} Module 5 displays connected)")
    socketio.emit('DisplayUpdate', module5_data)
    
    # Also send directly to registered display module sockets if any
    if display_module_sockets:
        print(f"[{datetime.now()}] Sending DisplayUpdate to {len(display_module_sockets)} registered display sockets")
        for socket_id, module_id in display_module_sockets.items():
            try:
                socketio.emit('DisplayUpdate', module5_data, room=socket_id)
            except Exception as e:
                print(f"[WARNING] Failed to send to display socket {socket_id} ({module_id}): {e}")
    
    print(f"[{datetime.now()}] Module 5 data generated from Module 1 data and sent to dashboard")

@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video(data):
    """Receive video frames from Module 1"""
    module_id = data.get('module_id', 'unknown')
    print(f"[{datetime.now()}] Received Video Frame from {module_id}")
    
    # Auto-register module if not already registered (when receiving video frames)
    module_type = 'crowd_detection'
    if module_id != 'unknown' and module_id not in connected_modules[module_type]:
        connected_modules[module_type].append(module_id)
        # Save connection event to history
        add_connection_event(module_id, module_type, 'connected')
        print(f"[{datetime.now()}] Auto-registered module from video frame: {module_id} ({module_type})")
        
        # Notify dashboard of new connection
        socketio.emit('module_connected', {
            'module_id': module_id,
            'module_type': module_type,
            'timestamp': datetime.now().isoformat()
        })
    
    # Extract video_frame from nested data structure and put it at top level
    # Client sends: {'module_id': ..., 'data': {'video_frame': '...', ...}}
    # Frontend expects: {'module_id': ..., 'video_frame': '...', 'data': {...}}
    video_frame_data = data.copy()
    if 'data' in data and isinstance(data['data'], dict):
        # Extract video_frame from nested data if it exists
        if 'video_frame' in data['data']:
            video_frame_data['video_frame'] = data['data']['video_frame']
            print(f"[{datetime.now()}] Extracted video frame ({len(data['data']['video_frame'])} bytes) from nested data")
    
    # Update current data if video frame includes crowd data
    # But preserve AI analysis data if it's recent and Module 1 data is empty/old
    if 'data' in data and data['data']:
        incoming_people_count = data.get('data', {}).get('people_count', 0)
        
        # Check if we have AI analysis data that should be preserved
        existing_crowd = current_data.get('crowd')
        is_ai_analysis = existing_crowd and existing_crowd.get('_ai_analysis', False)
        
        if is_ai_analysis:
            # Check how old the AI analysis is
            ai_timestamp = existing_crowd.get('_ai_timestamp')
            if isinstance(ai_timestamp, str):
                try:
                    ai_timestamp = datetime.fromisoformat(ai_timestamp.replace('Z', '+00:00'))
                except:
                    ai_timestamp = datetime.now()
            elif not isinstance(ai_timestamp, datetime):
                # Try to get from timestamp field
                timestamp_str = existing_crowd.get('timestamp')
                if timestamp_str:
                    try:
                        ai_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        ai_timestamp = datetime.now()
                else:
                    ai_timestamp = datetime.now()
            
            # Calculate time difference (handle timezone-aware datetimes)
            now = datetime.now()
            if ai_timestamp.tzinfo:
                now = datetime.now(ai_timestamp.tzinfo)
            time_since_ai = (now - ai_timestamp).total_seconds()
            
            # Preserve AI analysis if:
            # 1. It's less than 30 seconds old, AND
            # 2. Incoming Module 1 data has 0 people (empty/old data)
            if time_since_ai < 30 and incoming_people_count == 0:
                ai_people_count = existing_crowd.get('data', {}).get('people_count', 0)
                print(f"[{datetime.now()}] Preserving AI analysis data (people_count={ai_people_count}, {time_since_ai:.1f}s old) over Module 1 empty data")
                # Don't overwrite, but still emit the video frame for display
            else:
                # AI analysis is old or Module 1 has valid data - update normally
                if current_data['crowd']:
                    current_data['crowd'].update(data)
                else:
                    current_data['crowd'] = data
<<<<<<< HEAD
                # Save to persistent storage
                if 'data' in data and data['data']:
                    people_count = data.get('data', {}).get('people_count', 0)
                    timestamp_str = data.get('timestamp')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except:
                            timestamp = datetime.now()
                    else:
                        timestamp = datetime.now()
                    global historical_data
                    historical_data = add_crowd_entry(people_count, timestamp, full_data=data)
                
                # Add to minute buffer if we have crowd data
                if 'data' in data and data['data']:
                    people_count = data['data'].get('people_count', 0)
                    noise_db = data['data'].get('noise_db')
                    timestamp = datetime.now()
                    
                    add_to_buffer('module1_crowd', {
                        'people_count': people_count,
                        'noise_db': noise_db,
                        'timestamp': timestamp
                    })
                    
                    if noise_db is not None:
                        add_to_buffer('module1_audio', {
                            'noise_db': noise_db,
                            'timestamp': timestamp
                        })
        else:
            # No AI analysis to preserve - update normally
            if current_data['crowd']:
                current_data['crowd'].update(data)
            else:
                current_data['crowd'] = data
<<<<<<< HEAD
            # Save to persistent storage
            if 'data' in data and data['data']:
                people_count = data.get('data', {}).get('people_count', 0)
                timestamp_str = data.get('timestamp')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
                global historical_data
                historical_data = add_crowd_entry(people_count, timestamp, full_data=data)
            
            # Add to minute buffer if we have crowd data
            if 'data' in data and data['data']:
                people_count = data['data'].get('people_count', 0)
                noise_db = data['data'].get('noise_db')
                timestamp = datetime.now()
                
                add_to_buffer('module1_crowd', {
                    'people_count': people_count,
                    'noise_db': noise_db,
                    'timestamp': timestamp
                })
                
                if noise_db is not None:
                    add_to_buffer('module1_audio', {
                        'noise_db': noise_db,
                        'timestamp': timestamp
                    })
    
    # Emit with video_frame at top level for frontend
    socketio.emit('crowd_video_update', video_frame_data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data
    # This ensures Module 5 gets updated when video frame data arrives
    if 'data' in data and data['data']:
        court_id = data.get('court_id', 'basketball_a')
        # Use current crowd data (which may have been updated above) with historical fallback
        crowd_data_for_module5 = current_data.get('crowd') or get_latest_crowd_data()
        env_data_for_module5 = current_data.get('environment') or get_latest_environment_data()
        feedback_data_for_module5 = current_data.get('feedback') if current_data.get('feedback') else get_recent_feedback_data(10)
        
        module5_data = generate_module5_from_modules(
            court_id=court_id,
            crowd_data=crowd_data_for_module5,
            env_data=env_data_for_module5,
            feedback_data=feedback_data_for_module5 if feedback_data_for_module5 else None
        )
        socketio.emit('DisplayUpdate', module5_data)
        print(f"[{datetime.now()}] Module 5 data generated from Module 1 video frame and sent to dashboard")

# --- MODULE 2: ENVIRONMENT DATA ---
@socketio.on('EnvironmentDataEvent')
def handle_environment_data(data):
    """Receive environment sensor data from Module 2"""
    print(f"[{datetime.now()}] Received Environment Data: {data}")
    current_data['environment'] = data
    
<<<<<<< HEAD
    # Update module status
    module_id = data.get('module_id', 'unknown')
    update_module_status('environment', module_id, is_online=True)
    
    # Save to persistent storage with full historical records
    timestamp_str = data.get('timestamp')
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.now()
    else:
        timestamp = datetime.now()
    
    # Extract environment data for storage
    env_data_to_store = data.get('data', {}) if 'data' in data else data
    add_environment_entry(env_data_to_store, timestamp)
    
    # Add to minute buffer for averaging
    if 'data' in data:
        env_data = data['data']
        add_to_buffer('module2_env', {
            'temperature_c': env_data.get('temperature_c'),
            'humidity_percent': env_data.get('humidity_percent'),
            'pressure_hpa': env_data.get('pressure_hpa'),
            'uv_index': env_data.get('uv_index'),
            'voc_level': env_data.get('voc_level'),
            'comfort_score': env_data.get('comfort_score'),
            'timestamp': datetime.now()
        })
    
    socketio.emit('environment_update', data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data (with historical fallback)
    court_id = data.get('court_id', 'basketball_a')
    # Use historical data as fallback if current data is missing
    crowd_data_for_module5 = current_data.get('crowd') or get_latest_crowd_data()
    feedback_data_for_module5 = current_data.get('feedback') if current_data.get('feedback') else get_recent_feedback_data(10)
    
    module5_data = generate_module5_from_modules(
        court_id=court_id,
        crowd_data=crowd_data_for_module5,
        env_data=data,
        feedback_data=feedback_data_for_module5 if feedback_data_for_module5 else None
    )
    
    # Emit DisplayUpdate to all clients (including preview and Module 5 displays)
    connected_display_count = len(connected_modules['display'])
    print(f"[{datetime.now()}] Broadcasting DisplayUpdate from Module 2 to all clients ({connected_display_count} Module 5 displays connected)")
    socketio.emit('DisplayUpdate', module5_data)
    
    # Also send directly to registered display module sockets if any
    if display_module_sockets:
        print(f"[{datetime.now()}] Sending DisplayUpdate to {len(display_module_sockets)} registered display sockets")
        for socket_id, module_id in display_module_sockets.items():
            try:
                socketio.emit('DisplayUpdate', module5_data, room=socket_id)
            except Exception as e:
                print(f"[WARNING] Failed to send to display socket {socket_id} ({module_id}): {e}")
    
    print(f"[{datetime.now()}] Module 5 data generated from Module 2 data and sent to dashboard")

# --- MODULE 3: FEEDBACK DATA ---
@socketio.on('FeedbackStatusEvent')
def handle_feedback_status(data):
    """Receive kiosk status update from Module 3 (on/off based on proximity)"""
    module_id = data.get('module_id', 'unknown')
    is_active = data.get('is_active', False)
    status = 'active' if is_active else 'idle'
    distance = data.get('distance_cm')
    
    # Update module3_state and persist
    module3_state['kiosk_active'] = is_active
    save_module3_state()
    
    print(f"[{datetime.now()}] Module 3 Status: {module_id} is {status}" + 
          (f" (distance: {distance:.1f}cm)" if distance else ""))
    
    # Calculate time since last rating interaction
    time_since_last_rating = None
    if module3_state['last_rating_timestamp']:
        try:
            last_rating_dt = datetime.fromisoformat(module3_state['last_rating_timestamp'].replace('Z', '+00:00'))
            now = datetime.now(last_rating_dt.tzinfo) if last_rating_dt.tzinfo else datetime.now()
            time_diff = (now - last_rating_dt).total_seconds()
            
            # Format time difference
            if time_diff < 60:
                time_since_last_rating = f"{int(time_diff)}s ago"
            elif time_diff < 3600:
                time_since_last_rating = f"{int(time_diff // 60)}m ago"
            elif time_diff < 86400:
                time_since_last_rating = f"{int(time_diff // 3600)}h ago"
            else:
                time_since_last_rating = f"{int(time_diff // 86400)}d ago"
        except Exception as e:
            print(f"[WARNING] Error calculating time since last rating: {e}")
    
    # Emit status update to dashboard
    socketio.emit('feedback_status_update', {
        'module_id': module_id,
        'status': status,
        'is_active': is_active,
        'distance_cm': distance,
        'screen_on': is_active,
        'timestamp': datetime.now().isoformat(),
        'last_rating_timestamp': module3_state['last_rating_timestamp'],
        'latest_rating': module3_state['latest_rating'],
        'time_since_last_rating': time_since_last_rating
    })

@socketio.on('FeedbackDataEvent')
def handle_feedback_data(data):
    """Receive feedback data from Module 3"""
    print(f"[{datetime.now()}] Received Feedback Data: {data}")
    # Store feedback in list (keep last 50 entries in memory for quick access)
    current_data['feedback'].append(data)
    if len(current_data['feedback']) > 50:
        current_data['feedback'].pop(0)
    
    # Update module status
    module_id = data.get('module_id', 'unknown')
    update_module_status('feedback', module_id, is_online=True)
    
    # Save to persistent storage with full historical records
    timestamp_str = data.get('timestamp')
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.now()
    else:
        timestamp = datetime.now()
    
    add_feedback_entry(data, timestamp)
    
    # Track latest rating and timestamp if this is a rating interaction
    feedback_data = data.get('data', {})
    if feedback_data.get('report_type') == 'rating':
        rating = feedback_data.get('rating')
        if rating is not None:
            module3_state['latest_rating'] = rating
            module3_state['last_rating_timestamp'] = datetime.now().isoformat()
            save_module3_state()  # Persist state change
            print(f"[{datetime.now()}] Module 3: Latest rating updated to {rating}/5")
            
            # Save feedback immediately to database (not averaged)
            timestamp_str = datetime.now().isoformat()
            if USE_DATABASE:
                try:
                    conn = sqlite3.connect(HISTORY_DB)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO module3_feedback (timestamp, rating, report_type)
                        VALUES (?, ?, ?)
                    ''', (timestamp_str, rating, 'rating'))
                    conn.commit()
                    conn.close()
                    print(f"[INFO] Saved Module 3 feedback to database: rating={rating}")
                except Exception as e:
                    print(f"[ERROR] Failed to save Module 3 feedback: {e}")
    
    # Calculate average rating from all feedback entries
    ratings = []
    for feedback in current_data['feedback']:
        if feedback.get('data', {}).get('report_type') == 'rating':
            rating = feedback.get('data', {}).get('rating')
            if rating is not None:
                ratings.append(rating)
    
    average_rating = None
    total_ratings = len(ratings)
    if total_ratings > 0:
        average_rating = round(sum(ratings) / total_ratings, 2)
    
    # Create rating distribution for graph
    rating_distribution = {}
    for rating in ratings:
        rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
    
    # Calculate time since last rating interaction
    time_since_last_rating = None
    if module3_state['last_rating_timestamp']:
        try:
            last_rating_dt = datetime.fromisoformat(module3_state['last_rating_timestamp'].replace('Z', '+00:00'))
            now = datetime.now(last_rating_dt.tzinfo) if last_rating_dt.tzinfo else datetime.now()
            time_diff = (now - last_rating_dt).total_seconds()
            
            # Format time difference
            if time_diff < 60:
                time_since_last_rating = f"{int(time_diff)}s ago"
            elif time_diff < 3600:
                time_since_last_rating = f"{int(time_diff // 60)}m ago"
            elif time_diff < 86400:
                time_since_last_rating = f"{int(time_diff // 3600)}h ago"
            else:
                time_since_last_rating = f"{int(time_diff // 86400)}d ago"
        except Exception as e:
            print(f"[WARNING] Error calculating time since last rating: {e}")
    
    # Add calculated statistics to the update
    update_data = data.copy()
    update_data['statistics'] = {
        'average_rating': average_rating,
        'total_ratings': total_ratings,
        'rating_distribution': rating_distribution,
        'latest_rating': module3_state['latest_rating'],
        'last_rating_timestamp': module3_state['last_rating_timestamp'],
        'time_since_last_rating': time_since_last_rating,
        'kiosk_active': module3_state['kiosk_active']
    }
    
    socketio.emit('feedback_update', update_data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data (with historical fallback)
    # Use historical data as fallback if current data is missing
    crowd_data_for_module5 = current_data.get('crowd') or get_latest_crowd_data()
    env_data_for_module5 = current_data.get('environment') or get_latest_environment_data()
    
    if crowd_data_for_module5 or env_data_for_module5:
        court_id = data.get('court_id', 'basketball_a')
        feedback_data_for_module5 = current_data.get('feedback') if current_data.get('feedback') else get_recent_feedback_data(10)
        
        module5_data = generate_module5_from_modules(
            court_id=court_id,
            crowd_data=crowd_data_for_module5,
            env_data=env_data_for_module5,
            feedback_data=feedback_data_for_module5 if feedback_data_for_module5 else None
        )
        socketio.emit('DisplayUpdate', module5_data)
        print(f"[{datetime.now()}] Module 5 data generated from Module 3 data and sent to dashboard")

# --- Legacy Events (for backward compatibility) ---
@socketio.on('usage_data')
def handle_usage(data):
    """Legacy: Receive Rep Count from BeagleBone"""
    print(f"[{datetime.now()}] Received Usage Data: {data}")
    emit('update_bar_graph', data)

@socketio.on('volume_data')
def handle_volume(data):
    """Legacy: Receive Volume status from BeagleBone"""
    print(f"[{datetime.now()}] Received Volume Alert: {data}")
    emit('trigger_alert', data)

# --- Helper function for deep merging nested dictionaries ---
def deep_merge(base_dict, override_dict):
    """Recursively merge override_dict into base_dict"""
    result = base_dict.copy()
    for key, value in override_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

# --- Generate Module 5 Data from Modules 1-3 ---
def generate_module5_from_modules(court_id, crowd_data=None, env_data=None, feedback_data=None):
    """Generate Module 5 display data based on actual data from Modules 1-3
    
    Args:
        court_id: Court identifier (e.g., 'basketball_a')
        crowd_data: Data from Module 1 (crowd detection)
        env_data: Data from Module 2 (environment)
        feedback_data: Latest feedback from Module 3 (optional)
    """
    # Extract values from Modules 1-3 data
    people_count = 0
    crowd_level = 'empty'
    confidence = 0.85
    if crowd_data and 'data' in crowd_data:
        people_count = crowd_data['data'].get('people_count', 0)
        crowd_level = crowd_data['data'].get('crowd_level', 'empty')
        confidence = crowd_data['data'].get('confidence', 0.85)
    
    temp_c = 25
    humidity_percent = 50
    uv_index = 5
    comfort_score = 3.5
    voc_level = 'good'
    warnings = []
    if env_data and 'data' in env_data:
        temp_c = env_data['data'].get('temperature_c', 25)
        humidity_percent = env_data['data'].get('humidity_percent', 50)
        uv_index = env_data['data'].get('uv_index', 5)
        comfort_score = env_data['data'].get('comfort_score', 3.5)
        voc_level = env_data['data'].get('voc_level', 'good')
        warnings = env_data['data'].get('warnings', [])
    
    # Calculate estimated wait time based on crowd level
    wait_times = {
        'empty': 0,
        'light': 5,
        'normal': 10,
        'busy': 20,
        'full': 30
    }
    estimated_wait = wait_times.get(crowd_level, 10)
    
    # Get average rating from feedback (if available)
    rating_avg = 4.0
    if feedback_data and isinstance(feedback_data, list) and len(feedback_data) > 0:
        # Get last few feedback entries
        recent_feedback = feedback_data[-5:] if len(feedback_data) >= 5 else feedback_data
        ratings = [f['data'].get('rating') for f in recent_feedback if f.get('data', {}).get('report_type') == 'rating' and f['data'].get('rating')]
        if ratings:
            rating_avg = round(sum(ratings) / len(ratings), 1)
    
    occupancy = min(1.0, people_count / 10.0)
    current_hour = datetime.now().hour
    capacity = 10  # Default capacity
    
    # Load historical data (don't update here - only update when NEW data arrives)
    global historical_data
    historical_data = load_history()
    
    # Get hourly pattern from actual historical data (calculated server-side)
    today_hourly = get_today_hourly_pattern(historical_data, current_hour, people_count, capacity)
    
    # Get weekly pattern from actual historical data (calculated server-side)
    week_same_time = get_weekly_pattern(historical_data, current_hour, people_count, capacity)
    
    # Generate alternatives (fewer if current court is busy)
    num_alternatives = 2 if occupancy < 0.7 else 3
    alternatives = []
    alt_names = ['Court B', 'Court C', 'Court D']
    alt_statuses = ['light', 'normal', 'busy']
    for i in range(min(num_alternatives, 3)):
        # Alternative courts have lower occupancy
        alt_occupancy = max(0.1, occupancy * (0.3 + i * 0.2))
        alternatives.append({
            'id': f'basketball_{chr(98+i)}',
            'name': alt_names[i],
            'distance_m': 200 + (i * 300),
            'occupancy': alt_occupancy,
            'people': max(1, int(people_count * alt_occupancy / occupancy)) if occupancy > 0 else i + 1,
            'status': alt_statuses[i % len(alt_statuses)]
        })
    
    # Build recommendations based on current state
    best_times = []
    avoid_times = []
    next_slot = None
    
    if occupancy < 0.5:
        best_times = ['Now', 'Next hour']
        next_slot = 'Available now'
    elif occupancy < 0.8:
        best_times = ['Early morning', 'Evening']
        next_slot = f'{current_hour + 1}:00' if current_hour < 21 else 'Tomorrow 8:00'
    else:
        best_times = ['Early morning (6-8 AM)', 'Late evening (8-10 PM)']
        avoid_times = ['Peak hours (12-6 PM)']
        next_slot = f'{current_hour + 2}:00' if current_hour < 20 else 'Tomorrow 8:00'
    
    # Build Module 5 data structure
    module5_data = {
        'court_id': court_id,
        'timestamp': datetime.now().isoformat(),
        'current': {
            'occupancy': occupancy,
            'people_count': people_count,
            'crowd_level': crowd_level,
            'estimated_wait_min': estimated_wait,
            'confidence': confidence,
            'last_update': 'Just now'
        },
        'weather': {
            'temp_c': temp_c,
            'humidity_percent': humidity_percent,
            'uv_index': uv_index,
            'voc_level': voc_level,
            'comfort_score': comfort_score,
            'warnings': warnings,
            'recommendations': ['sunscreen', 'hydration'] if uv_index > 7 else ['hydration'] if temp_c > 30 else []
        },
        'patterns': {
            'today_hourly': today_hourly,
            'week_same_time': week_same_time
        },
        'recommendations': {
            'best_times_today': best_times,
            'avoid_times': avoid_times,
            'next_available_slot': next_slot,
            'nearby_alternatives': alternatives
        },
        'info': {
            'court_name': 'Basketball Court A',
            'type': 'outdoor',
            'surface': 'Concrete',
            'lighting_hours': '6AM-10PM',
            'rating_avg': rating_avg,
            'rating_count': 47,
            'last_cleaned': 'Today',
            'size': 'Full court',
            'capacity': 10,
            'facilities': ['Water', 'Seating', 'Restroom', 'Parking']
        }
    }
    
    return module5_data

# --- Generate Module 5 Test Data ---
def generate_module5_test_data(court_id, scenario='normal', custom_data=None):
    """Generate simulated test data for Module 5 based on scenario
    
    Args:
        court_id: Court identifier (e.g., 'basketball_a')
        scenario: Scenario name ('normal', 'full', 'empty', 'busy', 'custom')
        custom_data: Optional dict to override specific fields. Can override:
            - Top-level params: people, level, temp, wait, humidity, uv, comfort, rating, etc.
            - Nested fields using dot notation keys or nested dicts:
              Example: {'current': {'people_count': 8}, 'weather': {'temp_c': 35}}
              Or: {'current.people_count': 8, 'weather.temp_c': 35}
    """
    scenarios = {
        'normal': {
            'people': 5, 'level': 'normal', 'temp': 28, 'wait': 10,
            'humidity': 60, 'uv': 6, 'comfort': 3.5, 'rating': 4.2,
            'hourly_peak': 0.65, 'weekly_peak': 0.75, 'alternatives': 2
        },
        'full': {
            'people': 9, 'level': 'full', 'temp': 32, 'wait': 30,
            'humidity': 70, 'uv': 9, 'comfort': 2.5, 'rating': 3.8,
            'hourly_peak': 0.95, 'weekly_peak': 0.90, 'alternatives': 3
        },
        'empty': {
            'people': 0, 'level': 'empty', 'temp': 25, 'wait': 0,
            'humidity': 50, 'uv': 4, 'comfort': 4.5, 'rating': 4.8,
            'hourly_peak': 0.15, 'weekly_peak': 0.20, 'alternatives': 1
        },
        'busy': {
            'people': 7, 'level': 'busy', 'temp': 30, 'wait': 20,
            'humidity': 65, 'uv': 8, 'comfort': 3.0, 'rating': 4.0,
            'hourly_peak': 0.80, 'weekly_peak': 0.85, 'alternatives': 2
        }
    }
    
    params = scenarios.get(scenario, scenarios['normal']).copy()
    
    # Initialize override dictionaries
    nested_overrides = {}
    top_level_overrides = {}
    
    # Override with custom data if provided (for top-level params)
    if custom_data:
        # Handle dot notation keys (e.g., 'current.people_count': 8)
        for key, value in custom_data.items():
            if '.' in key:
                # Dot notation - convert to nested dict
                parts = key.split('.')
                current = nested_overrides
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            elif isinstance(value, dict):
                # Already nested dict
                nested_overrides[key] = value
            else:
                # Top-level param override
                top_level_overrides[key] = value
        
        # Apply top-level overrides to params
        params.update(top_level_overrides)
    
    occupancy = min(1.0, params['people'] / 10.0)
    current_hour = datetime.now().hour
    
    # Generate hourly pattern
    today_hourly = []
    for hour in range(8, 22):  # 8 AM to 10 PM
        if hour < current_hour:
            base_occupancy = params['hourly_peak'] * (1.0 - abs(hour - 14) / 6.0 * 0.5)
            today_hourly.append({'hour': hour, 'occupancy': min(1.0, max(0.1, base_occupancy))})
        elif hour == current_hour:
            today_hourly.append({'hour': hour, 'occupancy': occupancy})
        else:
            base_occupancy = params['hourly_peak'] * (1.0 - abs(hour - 14) / 6.0 * 0.5)
            today_hourly.append({'hour': hour, 'occupancy': min(1.0, max(0.1, base_occupancy))})
    
    # Weekly pattern
    week_same_time = [
        {'day': 'Mon', 'occupancy': params['weekly_peak'] * 0.9},
        {'day': 'Tue', 'occupancy': params['weekly_peak'] * 0.85},
        {'day': 'Wed', 'occupancy': params['weekly_peak']},
        {'day': 'Thu', 'occupancy': params['weekly_peak'] * 0.95},
        {'day': 'Fri', 'occupancy': params['weekly_peak'] * 1.0},
        {'day': 'Sat', 'occupancy': params['weekly_peak'] * 0.75},
        {'day': 'Sun', 'occupancy': params['weekly_peak'] * 0.5}
    ]
    
    # Generate alternatives
    alternatives = []
    alt_names = ['Court B', 'Court C', 'Court D']
    alt_statuses = ['light', 'normal', 'busy']
    for i in range(min(params['alternatives'], 3)):
        alternatives.append({
            'id': f'basketball_{chr(98+i)}',
            'name': alt_names[i],
            'distance_m': 200 + (i * 300),
            'occupancy': 0.2 + (i * 0.15),
            'people': i + 2,
            'status': alt_statuses[i % len(alt_statuses)]
        })
    
    # Build base data structure
    base_data = {
        'court_id': court_id,
        'timestamp': datetime.now().isoformat(),
        'current': {
            'occupancy': occupancy,
            'people_count': params['people'],
            'crowd_level': params['level'],
            'estimated_wait_min': params['wait'],
            'confidence': 0.92,
            'last_update': '30 seconds ago'
        },
        'weather': {
            'temp_c': params['temp'],
            'humidity_percent': params['humidity'],
            'uv_index': params['uv'],
            'voc_level': 'good',
            'comfort_score': params['comfort'],
            'warnings': ['high_uv'] if params['uv'] > 7 else [],
            'recommendations': ['sunscreen', 'hydration'] if params['uv'] > 7 else ['hydration']
        },
        'patterns': {
            'today_hourly': today_hourly,
            'week_same_time': week_same_time
        },
        'recommendations': {
            'best_times_today': ['07:00-09:00', '20:00-22:00'],
            'avoid_times': ['17:00-19:00'],
            'next_available_slot': '16:15',
            'nearby_alternatives': alternatives
        },
        'info': {
            'court_name': 'Basketball Court A',
            'type': 'outdoor',
            'surface': 'Concrete',
            'lighting_hours': '6AM-10PM',
            'rating_avg': params['rating'],
            'rating_count': 47,
            'last_cleaned': 'Today',
            'size': 'Full court',
            'capacity': 10,
            'facilities': ['Water', 'Seating', 'Restroom', 'Parking']
        }
    }
    
    # Apply nested overrides (from dot notation or nested dicts)
    if nested_overrides:
        base_data = deep_merge(base_data, nested_overrides)
    
    return base_data

# --- MODULE 5: Send Test Data to Display ---
@socketio.on('send_test_data_module5')
def handle_send_test_data_module5(data):
    """Send simulated test data to Module 5 displays (triggered from dashboard)
    
    Expected data format:
    {
        'court_id': 'basketball_a',  # Optional, defaults to 'basketball_a'
        'scenario': 'normal',  # 'normal', 'full', 'empty', 'busy', 'custom'
        'custom_data': {  # Optional - customize individual fields
            # Method 1: Nested dict format
            'current': {'people_count': 8, 'crowd_level': 'busy'},
            'weather': {'temp_c': 35, 'uv_index': 10},
            'info': {'rating_avg': 4.5},
            
            # Method 2: Dot notation format
            'current.people_count': 8,
            'weather.temp_c': 35,
            'current.estimated_wait_min': 15,
            'info.rating_avg': 4.5,
            
            # Method 3: Top-level params (affects scenario generation)
            'people': 8, 'temp': 35, 'level': 'busy'
        }
    }
    
    Examples:
    - Send normal scenario: {'scenario': 'normal'}
    - Custom people count: {'scenario': 'normal', 'custom_data': {'current.people_count': 8}}
    - Custom temperature: {'scenario': 'normal', 'custom_data': {'weather.temp_c': 40}}
    - Multiple customizations: {'scenario': 'normal', 'custom_data': {
        'current.people_count': 8,
        'weather.temp_c': 35,
        'info.rating_avg': 4.8
    }}
    """
    court_id = data.get('court_id', 'basketball_a')
    test_scenario = data.get('scenario', 'normal')  # 'normal', 'full', 'empty', 'busy', 'custom'
    custom_data = data.get('custom_data', None)
    
    print(f"[{datetime.now()}] Sending test data to Module 5: {test_scenario} (court: {court_id})")
    if custom_data:
        print(f"  Custom overrides: {json.dumps(custom_data, indent=2)}")
    
    # Generate test data based on scenario
    test_data = generate_module5_test_data(court_id, test_scenario, custom_data)
    
    # Send to Module 5 displays via DisplayUpdate event
    connected_display_count = len(connected_modules['display'])
    print(f"[{datetime.now()}] Broadcasting DisplayUpdate test data to all clients ({connected_display_count} Module 5 displays connected)")
    socketio.emit('DisplayUpdate', test_data)
    
    # Also send directly to registered display module sockets if any
    if display_module_sockets:
        print(f"[{datetime.now()}] Sending DisplayUpdate to {len(display_module_sockets)} registered display sockets")
        for socket_id, module_id in display_module_sockets.items():
            try:
                socketio.emit('DisplayUpdate', test_data, room=socket_id)
            except Exception as e:
                print(f"[WARNING] Failed to send to display socket {socket_id} ({module_id}): {e}")
    
    # Notify dashboard of successful send
    socketio.emit('test_data_sent', {
        'scenario': test_scenario,
        'court_id': court_id,
        'timestamp': datetime.now().isoformat()
    })
    
    return {'status': 'success', 'scenario': test_scenario}

# --- Mock Mode Control Events ---
@socketio.on('start_mock_data')
def handle_start_mock(data=None):
    """Start generating mock data"""
    if not mock_state['active']:
        mock_state['active'] = True
        
        # Get configuration from request
        if data:
            mock_state['scenario'] = data.get('scenario', 'normal')
            mock_state['update_interval'] = data.get('update_interval', 30)
        
        # Start background thread
        thread = threading.Thread(target=mock_data_loop, daemon=True)
        thread.start()
        mock_state['threads'].append(thread)
        
        print(f"[{datetime.now()}] Mock mode started (scenario: {mock_state['scenario']}, interval: {mock_state['update_interval']}s)")
        
        # Register mock modules
        for module_type in ['crowd_detection', 'environment', 'feedback']:
            module_id = f"mock_module_{module_type}"
            if module_id not in connected_modules[module_type]:
                connected_modules[module_type].append(module_id)
                socketio.emit('module_connected', {
                    'module_id': module_id,
                    'module_type': module_type,
                    'timestamp': datetime.now().isoformat()
                })
        
        return {'status': 'success', 'message': 'Mock mode started'}
    else:
        return {'status': 'info', 'message': 'Mock mode already active'}

@socketio.on('stop_mock_data')
def handle_stop_mock(data=None):
    """Stop generating mock data"""
    if mock_state['active']:
        mock_state['active'] = False
        print(f"[{datetime.now()}] Mock mode stopped")
        
        # Remove mock modules from connected list
        for module_type in connected_modules:
            connected_modules[module_type] = [
                m for m in connected_modules[module_type] if not m.startswith('mock_module')
            ]
        
        # Clear simulated data from current_data
        if current_data.get('crowd') and current_data['crowd'].get('module_id', '').startswith('mock_module'):
            current_data['crowd'] = None
            socketio.emit('crowd_update', {'cleared': True})
            print(f"[{datetime.now()}] Cleared mock crowd data")
        
        if current_data.get('environment') and current_data['environment'].get('module_id', '').startswith('mock_module'):
            current_data['environment'] = None
            socketio.emit('environment_update', {'cleared': True})
            print(f"[{datetime.now()}] Cleared mock environment data")
        
        # Clear mock feedback entries
        if current_data.get('feedback'):
            current_data['feedback'] = [
                f for f in current_data['feedback'] 
                if not f.get('module_id', '').startswith('mock_module')
            ]
            if current_data['feedback']:
                socketio.emit('feedback_update', current_data['feedback'][-1])
            else:
                socketio.emit('feedback_update', {'cleared': True})
            print(f"[{datetime.now()}] Cleared mock feedback data")
        
        # Stop sending Module 5 data (send empty/cleared state)
        # Generate empty Module 5 data to signal "disconnect"
        empty_module5 = {
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'current': {
                'occupancy': 0,
                'people_count': 0,
                'crowd_level': 'empty',
                'estimated_wait_min': 0,
                'confidence': 0,
                'last_update': 'No data'
            },
            'weather': {
                'temp_c': None,
                'humidity_percent': None,
                'uv_index': None,
                'voc_level': 'unknown',
                'comfort_score': None,
                'warnings': []
            },
            'info': {
                'court_name': 'Basketball Court A',
                'type': 'outdoor',
                'surface': 'Concrete',
                'rating_avg': None,
                'capacity': 10
            },
            'recommendations': {
                'next_available_slot': 'N/A',
                'nearby_alternatives': []
            },
            'patterns': {
                'today_hourly': [],
                'week_same_time': []
            },
            'disconnected': True
        }
        socketio.emit('DisplayUpdate', empty_module5)
        print(f"[{datetime.now()}] Sent Module 5 disconnect signal")
        
        return {'status': 'success', 'message': 'Mock mode stopped'}
    else:
        return {'status': 'info', 'message': 'Mock mode not active'}

@socketio.on('update_mock_config')
def handle_update_mock_config(data):
    """Update mock mode configuration without restarting"""
    if data.get('scenario'):
        mock_state['scenario'] = data['scenario']
        print(f"[{datetime.now()}] Mock scenario changed to: {mock_state['scenario']}")
    
    if data.get('update_interval'):
        mock_state['update_interval'] = data['update_interval']
        print(f"[{datetime.now()}] Mock update interval changed to: {mock_state['update_interval']}s")
    
    return {'status': 'success', 'config': {
        'scenario': mock_state['scenario'],
        'update_interval': mock_state['update_interval'],
        'active': mock_state['active']
    }}

@socketio.on('send_mock_data_once')
def handle_send_mock_data_once(data=None):
    """Send mock data once for all 3 modules (triggered manually from dashboard)"""
    scenario = data.get('scenario', 'normal') if data else mock_state.get('scenario', 'normal')
    
    print(f"[{datetime.now()}] Sending mock data once (scenario: {scenario})")
    
    # Generate mock data for all three modules
    crowd_data = generate_mock_crowd_data(scenario)
    env_data = generate_mock_environment_data(scenario)
    feedback_data = generate_mock_feedback_data(scenario)
    
    # Process through handlers to ensure data is saved to persistent storage
    handle_crowd_data(crowd_data)
    handle_environment_data(env_data)
    handle_feedback_data(feedback_data)
    
    print(f"[{datetime.now()}] Emitted crowd_update, environment_update, feedback_update events")
    
    # Generate and send Module 5 data (with historical fallback for feedback)
    court_id = 'basketball_a'
    feedback_data_for_module5 = current_data.get('feedback') if current_data.get('feedback') else get_recent_feedback_data(10)
    
    module5_data = generate_module5_from_modules(
        court_id=court_id,
        crowd_data=crowd_data,
        env_data=env_data,
        feedback_data=feedback_data_for_module5 if feedback_data_for_module5 else None
    )
    
    # Emit DisplayUpdate to all clients
    connected_display_count = len(connected_modules['display'])
    print(f"[{datetime.now()}] Broadcasting DisplayUpdate to all clients ({connected_display_count} Module 5 displays connected)")
    socketio.emit('DisplayUpdate', module5_data)
    
    # Also send directly to registered display module sockets if any
    if display_module_sockets:
        print(f"[{datetime.now()}] Sending DisplayUpdate to {len(display_module_sockets)} registered display sockets")
        for socket_id, module_id in display_module_sockets.items():
            try:
                socketio.emit('DisplayUpdate', module5_data, room=socket_id)
            except Exception as e:
                print(f"[WARNING] Failed to send to display socket {socket_id} ({module_id}): {e}")
    
    print(f"[{datetime.now()}] Mock data sent for all 3 modules and Module 5")
    
    return {'status': 'success', 'message': f'Mock data sent (scenario: {scenario})'}

# --- Connection Events ---
@socketio.on('connect')
def test_connect():
    print(f'[{datetime.now()}] Client Connected: {request.sid}')
    # Send current data to newly connected client
    emit('current_data_snapshot', current_data)
    # Send mock mode status
    emit('mock_status', {
        'active': mock_state['active'],
        'scenario': mock_state['scenario'],
        'update_interval': mock_state['update_interval']
    })
    # Send current Module 5 display connection status
    emit('module5_display_status', {
        'connected': len(connected_modules['display']) > 0,
        'count': len(connected_modules['display']),
        'modules': connected_modules['display']
    })

@socketio.on('disconnect')
def test_disconnect():
    socket_id = request.sid
    print(f'[{datetime.now()}] Client Disconnected: {socket_id}')
    
    # Check if this was a display module
    if socket_id in display_module_sockets:
        module_id = display_module_sockets[socket_id]
        module_type = 'display'
        # Remove from connected modules
        if module_id in connected_modules['display']:
            connected_modules['display'].remove(module_id)
        # Remove from socket tracking
        del display_module_sockets[socket_id]
        
        # Update module status to offline
        update_module_status(module_type, module_id, is_online=False)
        
        # Save disconnection event to history
        add_connection_event(module_id, module_type, 'disconnected')
        
        # Emit disconnect event for Module 5
        socketio.emit('module5_display_disconnected', {
            'module_id': module_id,
            'timestamp': datetime.now().isoformat(),
            'count': len(connected_modules['display'])
        })
        print(f"[{datetime.now()}] Module 5 display disconnected: {module_id}")
<<<<<<< HEAD
    else:
        # Try to find and mark other module types as offline
        # Note: We need to track socket_id to module_id mapping for non-display modules
        # For now, we'll mark modules as offline based on connection history
        # In a production system, you'd maintain a socket_id -> module_id mapping
        pass
    
    # Check if this was a feedback module (Module 3)
    if socket_id in feedback_module_sockets:
        module_id = feedback_module_sockets[socket_id]
        # Remove from connected modules
        if module_id in connected_modules['feedback']:
            connected_modules['feedback'].remove(module_id)
        # Remove from socket tracking
        del feedback_module_sockets[socket_id]
        
        # Set kiosk to idle but preserve all data
        module3_state['kiosk_active'] = False
        
        # Calculate time since last rating interaction (preserve data)
        time_since_last_rating = None
        if module3_state['last_rating_timestamp']:
            try:
                last_rating_dt = datetime.fromisoformat(module3_state['last_rating_timestamp'].replace('Z', '+00:00'))
                now = datetime.now(last_rating_dt.tzinfo) if last_rating_dt.tzinfo else datetime.now()
                time_diff = (now - last_rating_dt).total_seconds()
                
                # Format time difference
                if time_diff < 60:
                    time_since_last_rating = f"{int(time_diff)}s ago"
                elif time_diff < 3600:
                    time_since_last_rating = f"{int(time_diff // 60)}m ago"
                elif time_diff < 86400:
                    time_since_last_rating = f"{int(time_diff // 3600)}h ago"
                else:
                    time_since_last_rating = f"{int(time_diff // 86400)}d ago"
            except Exception as e:
                print(f"[WARNING] Error calculating time since last rating: {e}")
        
        # Emit status update to set kiosk to idle, but keep all data
        socketio.emit('feedback_status_update', {
            'module_id': module_id,
            'status': 'idle',
            'is_active': False,
            'distance_cm': None,
            'screen_on': False,
            'timestamp': datetime.now().isoformat(),
            'last_rating_timestamp': module3_state['last_rating_timestamp'],
            'latest_rating': module3_state['latest_rating'],
            'time_since_last_rating': time_since_last_rating
        })
        print(f"[{datetime.now()}] Module 3 (feedback) disconnected: {module_id} - Status set to idle")
>>>>>>> 5cbae18 (Add history system implementation)

if __name__ == '__main__':
    import socket
    # Print Anthropic client status on startup
    print("=" * 60)
    print("SERVER STARTUP - Anthropic AI Status:")
    if anthropic_client:
        print(f"  ✓ Anthropic client initialized successfully")
        print(f"  ✓ AI image analysis: ENABLED")
    else:
        print(f"  ✗ Anthropic client: NOT INITIALIZED")
        print(f"  ✗ AI image analysis: DISABLED")
        if not ANTHROPIC_AVAILABLE:
            print(f"  → Reason: anthropic library not installed")
        else:
            print(f"  → Reason: API key not found")
    print("=" * 60)
    
    # Get the machine's hostname to determine IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("=" * 60)
    print("Starting Multi-Module Web Server")
    print("Listening for: Crowd, Environment, and Feedback modules")
    print(f"Server listening on: 0.0.0.0:5000 (all interfaces)")
    print(f"Access via: http://{local_ip}:5000 or http://192.168.72.161:5000")
    print("=" * 60)
    wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)

