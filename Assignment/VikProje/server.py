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
        }, broadcast=True)
        
        # Send log to dashboard
        socketio.emit('board_log', {
            'module_id': module_id,
            'module_type': module_type,
            'event': 'module_register',
            'timestamp': datetime.now().isoformat(),
            'data': data
        }, broadcast=True)

# --- MODULE 1: CROWD DETECTION DATA ---
@socketio.on('CrowdDataEvent')
def handle_crowd_data(data):
    """Receive crowd detection data from Module 1"""
    print(f"[{datetime.now()}] Received Crowd Data: {data}")
    current_data['crowd'] = data
    socketio.emit('crowd_update', data)
    # Send log to dashboard
    socketio.emit('board_log', {
        'module_id': data.get('module_id', 'unknown'),
        'module_type': 'crowd_detection',
        'event': 'CrowdDataEvent',
        'timestamp': datetime.now().isoformat(),
        'data': data
    }, broadcast=True)

@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video(data):
    """Receive video frames from Module 1"""
    print(f"[{datetime.now()}] Received Video Frame from {data.get('module_id', 'unknown')}")
    socketio.emit('crowd_video_update', data)
    # Send log to dashboard
    socketio.emit('board_log', {
        'module_id': data.get('module_id', 'unknown'),
        'module_type': 'crowd_detection',
        'event': 'CrowdVideoFrameEvent',
        'timestamp': datetime.now().isoformat(),
        'data': {'video_frame_size': len(data.get('data', {}).get('video_frame', '')) if data.get('data') else 0}
    }, broadcast=True)

# --- MODULE 2: ENVIRONMENT DATA ---
@socketio.on('EnvironmentDataEvent')
def handle_environment_data(data):
    """Receive environment sensor data from Module 2"""
    print(f"[{datetime.now()}] Received Environment Data: {data}")
    current_data['environment'] = data
    socketio.emit('environment_update', data)
    # Send log to dashboard
    socketio.emit('board_log', {
        'module_id': data.get('module_id', 'unknown'),
        'module_type': 'environment',
        'event': 'EnvironmentDataEvent',
        'timestamp': datetime.now().isoformat(),
        'data': data
    }, broadcast=True)

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
    # Send log to dashboard
    socketio.emit('board_log', {
        'module_id': data.get('module_id', 'unknown'),
        'module_type': 'feedback',
        'event': 'FeedbackDataEvent',
        'timestamp': datetime.now().isoformat(),
        'data': data
    }, broadcast=True)

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

# --- Generate Module 5 Test Data ---
def generate_module5_test_data(court_id, scenario='normal', custom_data=None):
    """Generate simulated test data for Module 5 based on scenario"""
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
    
    # Override with custom data if provided
    if custom_data:
        params.update(custom_data)
    
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
    
    # Determine warnings and recommendations based on UV and temperature
    warnings = []
    recommendations = []
    if params['uv'] > 7:
        warnings.append('high_uv')
        recommendations.extend(['use_sunscreen', 'stay_hydrated'])
    if params['temp'] > 30:
        warnings.append('high_heat')
        recommendations.append('play_after_6pm')
    if not recommendations:
        recommendations = ['stay_hydrated']
    
    # Determine VOC level based on comfort score
    voc_level = 'good'
    if params['comfort'] < 2.0:
        voc_level = 'poor'
    elif params['comfort'] < 3.0:
        voc_level = 'moderate'
    
    return {
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
            'pressure_hpa': 1013,  # Standard atmospheric pressure
            'uv_index': params['uv'],
            'voc_level': voc_level,
            'voc_reading': 200 if voc_level == 'good' else (300 if voc_level == 'moderate' else 500),
            'comfort_score': params['comfort'],
            'playable': params['comfort'] > 2.0,
            'warnings': warnings,
            'recommendations': recommendations
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
            'last_cleaned': datetime.now().replace(hour=8, minute=0).isoformat(),
            'size': 'Full court',
            'capacity': 10,
            'facilities': ['Water', 'Seating', 'Restroom', 'Parking']
        }
    }

# --- Generate Test Data for Each Module Type ---
def generate_crowd_test_data(scenario='normal'):
    """Generate test data for Crowd Detection module"""
    scenarios = {
        'empty': {'people': 0, 'level': 'empty', 'noise': 40, 'motion': False, 'proximity': False, 'confidence': 0.95},
        'light': {'people': 2, 'level': 'light', 'noise': 50, 'motion': True, 'proximity': False, 'confidence': 0.88},
        'normal': {'people': 5, 'level': 'normal', 'noise': 65, 'motion': True, 'proximity': True, 'confidence': 0.92},
        'busy': {'people': 7, 'level': 'busy', 'noise': 75, 'motion': True, 'proximity': True, 'confidence': 0.90},
        'full': {'people': 9, 'level': 'full', 'noise': 85, 'motion': True, 'proximity': True, 'confidence': 0.93}
    }
    params = scenarios.get(scenario, scenarios['normal'])
    
    return {
        'module_id': 'test_crowd_unit',
        'court_id': 'basketball_a',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'people_count': params['people'],
            'crowd_level': params['level'],
            'noise_db': params['noise'],
            'motion_detected': params['motion'],
            'proximity_triggered': params['proximity'],
            'confidence': params['confidence'],
            'sensors_status': {
                'webcam': 'ok',
                'mic': 'ok',
                'motion': 'ok',
                'proximity': 'ok'
            }
        }
    }

def generate_environment_test_data(scenario='normal'):
    """Generate test data for Environment module"""
    scenarios = {
        'cool': {'temp': 22, 'humidity': 50, 'uv': 3, 'voc': 'good', 'comfort': 4.5, 'warnings': []},
        'normal': {'temp': 28, 'humidity': 60, 'uv': 6, 'voc': 'good', 'comfort': 3.5, 'warnings': []},
        'hot': {'temp': 32, 'humidity': 70, 'uv': 9, 'voc': 'moderate', 'comfort': 2.5, 'warnings': ['high_uv', 'high_heat']},
        'extreme': {'temp': 35, 'humidity': 80, 'uv': 11, 'voc': 'poor', 'comfort': 1.5, 'warnings': ['high_uv', 'high_heat', 'poor_air']}
    }
    params = scenarios.get(scenario, scenarios['normal'])
    
    recommendations = []
    if params['uv'] > 7:
        recommendations.extend(['use_sunscreen', 'stay_hydrated'])
    if params['temp'] > 30:
        recommendations.append('play_after_6pm')
    if not recommendations:
        recommendations = ['hydration']
    
    return {
        'module_id': 'test_environment_unit',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'temperature_c': params['temp'],
            'humidity_percent': params['humidity'],
            'pressure_hpa': 1013,
            'voc_level': params['voc'],
            'voc_reading': 200 if params['voc'] == 'good' else (300 if params['voc'] == 'moderate' else 500),
            'uv_index': params['uv'],
            'comfort_score': params['comfort'],
            'playable': params['comfort'] > 2.0,
            'warnings': params['warnings'],
            'recommendations': recommendations
        }
    }

def generate_feedback_test_data(feedback_type='rating', rating_value=4):
    """Generate test data for Feedback module"""
    if feedback_type == 'rating':
        return {
            'module_id': 'test_feedback_kiosk',
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'rating',
                'question_id': 'overall_quality',
                'question_text': 'How would you rate the overall court quality?',
                'rating': rating_value,
                'rating_scale': '1-5',
                'interaction_time_seconds': 8,
                'gesture_used': True
            }
        }
    else:  # text feedback
        issues = [
            {'text': 'Net is broken on the north side', 'category': 'net_broken', 'priority': 'medium'},
            {'text': 'Court surface has cracks', 'category': 'surface_damage', 'priority': 'high'},
            {'text': 'Lighting not working properly', 'category': 'lighting_issue', 'priority': 'medium'},
            {'text': 'Basketball rim is loose', 'category': 'equipment_issue', 'priority': 'high'}
        ]
        issue = issues[rating_value % len(issues)] if isinstance(rating_value, int) else issues[0]
        
        return {
            'module_id': 'test_feedback_kiosk',
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'text',
                'question_id': 'maintenance_issue',
                'question_text': 'Report a maintenance issue',
                'text_response': issue['text'],
                'issue_category': issue['category'],
                'priority': issue['priority'],
                'interaction_time_seconds': 12,
                'gesture_used': True
            }
        }

# --- Send Test Data Handlers for Each Module ---
@socketio.on('send_test_data_crowd')
def handle_send_test_data_crowd(data):
    """Send test crowd data (triggered from dashboard)"""
    scenario = data.get('scenario', 'normal')
    print(f"[{datetime.now()}] Sending test crowd data: {scenario}")
    
    test_data = generate_crowd_test_data(scenario)
    
    # Update server's current data storage
    current_data['crowd'] = test_data
    
    # Emit to clients as if it came from a real module
    socketio.emit('crowd_update', test_data)
    
    socketio.emit('test_data_sent', {
        'module_type': 'crowd',
        'scenario': scenario,
        'timestamp': datetime.now().isoformat()
    })
    
    return {'status': 'success', 'scenario': scenario}

@socketio.on('send_test_data_environment')
def handle_send_test_data_environment(data):
    """Send test environment data (triggered from dashboard)"""
    scenario = data.get('scenario', 'normal')
    print(f"[{datetime.now()}] Sending test environment data: {scenario}")
    
    test_data = generate_environment_test_data(scenario)
    
    # Update server's current data storage
    current_data['environment'] = test_data
    
    # Emit to clients as if it came from a real module
    socketio.emit('environment_update', test_data)
    
    socketio.emit('test_data_sent', {
        'module_type': 'environment',
        'scenario': scenario,
        'timestamp': datetime.now().isoformat()
    })
    
    return {'status': 'success', 'scenario': scenario}

@socketio.on('send_test_data_feedback')
def handle_send_test_data_feedback(data):
    """Send test feedback data (triggered from dashboard)"""
    feedback_type = data.get('feedback_type', 'rating')  # 'rating' or 'text'
    rating_value = data.get('rating_value', 4)
    print(f"[{datetime.now()}] Sending test feedback data: {feedback_type} (value: {rating_value})")
    
    test_data = generate_feedback_test_data(feedback_type, rating_value)
    
    # Update server's current data storage
    current_data['feedback'].append(test_data)
    if len(current_data['feedback']) > 50:
        current_data['feedback'].pop(0)
    
    # Emit to clients as if it came from a real module
    socketio.emit('feedback_update', test_data)
    
    socketio.emit('test_data_sent', {
        'module_type': 'feedback',
        'feedback_type': feedback_type,
        'timestamp': datetime.now().isoformat()
    })
    
    return {'status': 'success', 'feedback_type': feedback_type}

# --- MODULE 5: Send Test Data to Display ---
@socketio.on('send_test_data_module5')
def handle_send_test_data_module5(data):
    """Send simulated test data to Module 5 displays (triggered from dashboard)"""
    court_id = data.get('court_id', 'basketball_a')
    test_scenario = data.get('scenario', 'normal')  # 'normal', 'full', 'empty', 'busy'
    custom_data = data.get('custom_data', None)
    
    print(f"[{datetime.now()}] Sending test data to Module 5: {test_scenario} (court: {court_id})")
    if custom_data:
        print(f"  Custom overrides: {custom_data}")
    
    # Generate test data based on scenario
    test_data = generate_module5_test_data(court_id, test_scenario, custom_data)
    
    # Send to Module 5 displays via DisplayUpdate event
    socketio.emit('DisplayUpdate', test_data)
    
    # Send log to dashboard showing what was sent
    socketio.emit('board_log', {
        'module_id': 'server',
        'module_type': 'display',
        'event': 'DisplayUpdate',
        'timestamp': datetime.now().isoformat(),
        'data': test_data
    })
    
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
    # Send log to dashboard
    socketio.emit('board_log', {
        'module_id': request.sid[:8],
        'module_type': 'client',
        'event': 'connect',
        'timestamp': datetime.now().isoformat(),
        'data': {'sid': request.sid}
    })

@socketio.on('disconnect')
def test_disconnect():
    print(f'[{datetime.now()}] Client Disconnected: {request.sid}')
    # Send log to dashboard
    socketio.emit('board_log', {
        'module_id': request.sid[:8],
        'module_type': 'client',
        'event': 'disconnect',
        'timestamp': datetime.now().isoformat(),
        'data': {'sid': request.sid}
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Multi-Module Web Server")
    print("Listening for: Crowd, Environment, and Feedback modules")
    print("Server URL: http://192.168.72.161:5000")
    print("=" * 60)
    wsgi.server(eventlet.listen(("192.168.72.161", 5000)), app)

