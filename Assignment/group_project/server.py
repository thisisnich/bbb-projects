from flask import Flask, render_template, request
import eventlet
from eventlet import wsgi
from flask_socketio import SocketIO, emit
from datetime import datetime
import json

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

# --- Connection Events ---
@socketio.on('connect')
def test_connect():
    print(f'[{datetime.now()}] Client Connected: {request.sid}')
    # Send current data to newly connected client
    emit('current_data_snapshot', current_data)

@socketio.on('disconnect')
def test_disconnect():
    print(f'[{datetime.now()}] Client Disconnected: {request.sid}')

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Multi-Module Web Server")
    print("Listening for: Crowd, Environment, and Feedback modules")
    print("Server URL: http://192.168.72.161:5000")
    print("=" * 60)
    wsgi.server(eventlet.listen(("192.168.72.161", 5000)), app)

