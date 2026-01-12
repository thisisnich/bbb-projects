from flask import Flask, render_template, request
import eventlet
from eventlet import wsgi
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import random
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# --- Data Storage ---
connected_modules = {
    'crowd_detection': [],
    'environment': [],
    'feedback': []
}

# Current data from each module type
current_data = {
    'crowd': None,
    'environment': None,
    'feedback': []
}

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
            
            # Generate and emit mock data for all three modules
            crowd_data = generate_mock_crowd_data(scenario)
            socketio.emit('crowd_update', crowd_data)
            current_data['crowd'] = crowd_data
            
            env_data = generate_mock_environment_data(scenario)
            socketio.emit('environment_update', env_data)
            current_data['environment'] = env_data
            
            # Generate feedback less frequently (30% chance)
            if random.random() < 0.3:
                feedback_data = generate_mock_feedback_data(scenario)
                socketio.emit('feedback_update', feedback_data)
                current_data['feedback'].append(feedback_data)
                if len(current_data['feedback']) > 50:
                    current_data['feedback'].pop(0)
            
            print(f"[{datetime.now()}] Mock data sent (scenario: {scenario})")
            
            # Wait for next update
            time.sleep(mock_state['update_interval'])
            
        except Exception as e:
            print(f"[{datetime.now()}] Error in mock data loop: {e}")
            break
    
    print(f"[{datetime.now()}] Mock data generator stopped")

@app.route('/')
def index():
    return render_template('index.html')

# --- Module Registration ---
@socketio.on('module_register')
def handle_module_register(data):
    """Register a module when it connects"""
    module_id = data.get('module_id', 'unknown')
    module_type = data.get('module_type', 'unknown')
    
    if module_type in connected_modules:
        if module_id not in connected_modules[module_type]:
            connected_modules[module_type].append(module_id)
        print(f"[{datetime.now()}] Module registered: {module_id} ({module_type})")
        
        # Notify dashboard of new connection
        socketio.emit('module_connected', {
            'module_id': module_id,
            'module_type': module_type,
            'timestamp': datetime.now().isoformat()
        })

# --- MODULE 1: CROWD DETECTION DATA ---
@socketio.on('CrowdDataEvent')
def handle_crowd_data(data):
    """Receive crowd detection data from Module 1"""
    print(f"[{datetime.now()}] Received Crowd Data: {data}")
    current_data['crowd'] = data
    socketio.emit('crowd_update', data)

@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video(data):
    """Receive video frames from Module 1"""
    print(f"[{datetime.now()}] Received Video Frame from {data.get('module_id', 'unknown')}")
    socketio.emit('crowd_video_update', data)

# --- MODULE 2: ENVIRONMENT DATA ---
@socketio.on('EnvironmentDataEvent')
def handle_environment_data(data):
    """Receive environment sensor data from Module 2"""
    print(f"[{datetime.now()}] Received Environment Data: {data}")
    current_data['environment'] = data
    socketio.emit('environment_update', data)

# --- MODULE 3: FEEDBACK DATA ---
@socketio.on('FeedbackDataEvent')
def handle_feedback_data(data):
    """Receive feedback data from Module 3"""
    print(f"[{datetime.now()}] Received Feedback Data: {data}")
    # Store feedback in list (keep last 50 entries)
    current_data['feedback'].append(data)
    if len(current_data['feedback']) > 50:
        current_data['feedback'].pop(0)
    socketio.emit('feedback_update', data)

# --- Legacy Events (for backward compatibility) ---
@socketio.on('usage_data')
def handle_usage(data):
    """Legacy: Receive Rep Count from BeagleBone"""
    print(f"[{datetime.now()}] Received Usage Data: {data}")
    emit('update_bar_graph', data, broadcast=True)

@socketio.on('volume_data')
def handle_volume(data):
    """Legacy: Receive Volume status from BeagleBone"""
    print(f"[{datetime.now()}] Received Volume Alert: {data}")
    emit('trigger_alert', data, broadcast=True)

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
    # Note: socketio.emit() broadcasts by default (no 'to' parameter means all clients)
    socketio.emit('DisplayUpdate', test_data)
    
    # Notify dashboard of successful send
    socketio.emit('test_data_sent', {
        'scenario': test_scenario,
        'court_id': court_id,
        'timestamp': datetime.now().isoformat()
    })
    
    return {'status': 'success', 'scenario': test_scenario}

# --- API Endpoint: Get Current Data ---
@app.route('/api/current_data')
def get_current_data():
    """REST API endpoint to get current data from all modules"""
    return json.dumps({
        'crowd': current_data['crowd'],
        'environment': current_data['environment'],
        'feedback': current_data['feedback'][-10:],  # Last 10 feedback entries
        'connected_modules': connected_modules,
        'timestamp': datetime.now().isoformat()
    }, indent=2)

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

@socketio.on('disconnect')
def test_disconnect():
    print(f'[{datetime.now()}] Client Disconnected: {request.sid}')

if __name__ == '__main__':
    import socket
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

