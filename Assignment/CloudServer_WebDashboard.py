"""
Cloud Server with Web Dashboard
Receives video frames from Module 1, processes with Google AI API,
and displays results on web dashboard
"""
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import eventlet
from eventlet import wsgi
import base64
import os
import json

# ========== CONFIGURATION ==========
SERVER_IP = '192.168.18.89'  # CHANGE THIS to your server IP
SERVER_PORT = 5000
GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')  # Set as environment variable

# ========== FLASK APP SETUP ==========
app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# ========== DATA STORAGE ==========
connected_modules = {
    'crowd_detection': [],
    'environment': [],
    'feedback': [],
    'dashboard': [],
    'display': []
}

crowd_data_history = []
current_crowd_data = {
    'people_count': 0,
    'crowd_level': 'unknown',
    'confidence': 0.0,
    'noise_db': 0,
    'motion_detected': False,
    'proximity_triggered': False,
    'timestamp': None
}

# ========== GOOGLE AI PROCESSING ==========

def process_image_with_google_ai(image_bytes):
    """
    Process image with Google AI API to count people
    Returns: number of people detected
    """
    try:
        if not GOOGLE_AI_API_KEY:
            print("[WARNING] Google AI API key not set. Using fallback.")
            return 0
        
        import google.generativeai as genai
        
        # Configure API
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        
        # Use Gemini Vision API
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Create prompt
        prompt = """Count the number of people visible in this image. 
        Look for human figures, faces, or people playing sports.
        Return ONLY a number, nothing else."""
        
        # Process image
        response = model.generate_content([prompt, {
            'mime_type': 'image/jpeg',
            'data': image_bytes
        }])
        
        # Extract number from response
        response_text = response.text.strip()
        # Try to extract number from response
        import re
        numbers = re.findall(r'\d+', response_text)
        if numbers:
            people_count = int(numbers[0])
            return max(0, people_count)  # Ensure non-negative
        else:
            print(f"[WARNING] Could not parse number from AI response: {response_text}")
            return 0
        
    except ImportError:
        print("[ERROR] google-generativeai not installed. Install with: pip install google-generativeai")
        return 0
    except Exception as e:
        print(f'[ERROR] Google AI API error: {e}')
        return 0

def calculate_confidence(people_count, noise_db, motion_detected, proximity_triggered):
    """Calculate confidence score based on multiple sensors"""
    confidence = 0.5  # Base confidence
    
    # If people detected, increase confidence
    if people_count > 0:
        confidence += 0.3
    
    # If noise level suggests activity
    if noise_db > 60:
        confidence += 0.1
    
    # If motion detected
    if motion_detected:
        confidence += 0.05
    
    # If proximity triggered
    if proximity_triggered:
        confidence += 0.05
    
    return min(1.0, confidence)  # Cap at 1.0

def determine_crowd_level(people_count):
    """Determine crowd level based on people count"""
    if people_count == 0:
        return 'empty'
    elif people_count <= 2:
        return 'light'
    elif people_count <= 5:
        return 'normal'
    elif people_count <= 8:
        return 'busy'
    else:
        return 'full'

def generate_module5_data(court_id, people_count, crowd_level, confidence):
    """Generate complete Module 5 display data structure"""
    occupancy = min(1.0, people_count / 10.0)  # Assume max 10 people = 100%
    
    # Generate hourly pattern for today
    current_hour = datetime.now().hour
    today_hourly = []
    for hour in range(8, 22):  # 8 AM to 10 PM
        if hour < current_hour:
            # Past data - simulate pattern
            base_occupancy = 0.3 + 0.4 * (abs(hour - 14) / 6.0)  # Peak at 2 PM
            today_hourly.append({'hour': hour, 'occupancy': min(1.0, base_occupancy + (0.2 if hour == current_hour - 1 else 0))})
        elif hour == current_hour:
            # Current hour
            today_hourly.append({'hour': hour, 'occupancy': occupancy})
        else:
            # Future - prediction
            base_occupancy = 0.3 + 0.4 * (abs(hour - 14) / 6.0)
            today_hourly.append({'hour': hour, 'occupancy': min(1.0, base_occupancy)})
    
    # Weekly pattern (same time of day)
    week_same_time = [
        {'day': 'Mon', 'occupancy': 0.75},
        {'day': 'Tue', 'occupancy': 0.65},
        {'day': 'Wed', 'occupancy': 0.90},
        {'day': 'Thu', 'occupancy': 0.85},
        {'day': 'Fri', 'occupancy': 0.95},
        {'day': 'Sat', 'occupancy': 0.70},
        {'day': 'Sun', 'occupancy': 0.45}
    ]
    
    # Estimate wait time
    if crowd_level == 'full':
        estimated_wait = 25
    elif crowd_level == 'busy':
        estimated_wait = 15
    elif crowd_level == 'normal':
        estimated_wait = 5
    else:
        estimated_wait = 0
    
    return {
        'court_id': court_id,
        'timestamp': datetime.now().isoformat(),
        'current': {
            'occupancy': occupancy,
            'people_count': people_count,
            'crowd_level': crowd_level,
            'estimated_wait_min': estimated_wait,
            'confidence': confidence,
            'last_update': '30 seconds ago'
        },
        'weather': {
            'temp_c': 30,
            'humidity_percent': 65,
            'uv_index': 9,
            'voc_level': 'good',
            'comfort_score': 3.2,
            'warnings': ['high_uv'],
            'recommendations': ['sunscreen', 'hydration']
        },
        'patterns': {
            'today_hourly': today_hourly,
            'week_same_time': week_same_time
        },
        'recommendations': {
            'best_times_today': ['07:00-09:00', '20:00-22:00'],
            'avoid_times': ['17:00-19:00'],
            'next_available_slot': '16:15',
            'nearby_alternatives': [
                {
                    'id': 'basketball_b',
                    'name': 'Court B',
                    'distance_m': 200,
                    'occupancy': 0.30,
                    'people': 3,
                    'status': 'light'
                },
                {
                    'id': 'basketball_c',
                    'name': 'Court C',
                    'distance_m': 500,
                    'occupancy': 0.0,
                    'people': 0,
                    'status': 'empty'
                }
            ]
        },
        'info': {
            'court_name': 'Basketball Court A',
            'type': 'outdoor',
            'surface': 'rubber',
            'lighting_hours': '18:00-22:00',
            'rating_avg': 4.2,
            'rating_count': 47,
            'last_cleaned': datetime.now().replace(hour=8, minute=0).isoformat(),
            'facilities': ['water_cooler', 'covered_seating', 'restrooms']
        }
    }

def generate_module5_test_data(court_id, scenario='normal', custom_data=None):
    """Generate simulated test data for Module 5 based on scenario
    
    Args:
        court_id: Court identifier
        scenario: Preset scenario ('normal', 'full', 'empty', 'busy', 'custom')
        custom_data: Optional dict with custom values to override defaults
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
    
    # Override with custom data if provided
    if custom_data:
        params.update(custom_data)
        # Ensure facilities is a list (handle both string and list inputs)
        if 'facilities' in params:
            if isinstance(params['facilities'], str):
                params['facilities'] = [f.strip() for f in params['facilities'].split(',') if f.strip()]
            elif not isinstance(params['facilities'], list):
                params['facilities'] = ['Water', 'Seating', 'Restroom', 'Parking']  # Default
    
    # Generate data with custom parameters
    occupancy = min(1.0, params['people'] / 10.0)
    current_hour = datetime.now().hour
    
    # Generate hourly pattern with custom peak
    # Check if custom hourly values were provided
    custom_hourly_raw = params.get('custom_hourly', {})
    
    # Convert string keys to integers (JavaScript sends keys as strings in JSON)
    custom_hourly = {}
    if custom_hourly_raw:
        for key, value in custom_hourly_raw.items():
            try:
                hour_int = int(key)  # Convert string '8' to int 8
                custom_hourly[hour_int] = float(value)  # Ensure value is float
            except (ValueError, TypeError):
                # Skip invalid entries
                continue
        if custom_hourly:
            print(f'[DEBUG] Custom hourly values converted: {custom_hourly}')
    
    today_hourly = []
    for hour in range(8, 22):  # 8 AM to 10 PM
        # Use custom value if provided, otherwise generate automatically
        if hour in custom_hourly:
            today_hourly.append({'hour': hour, 'occupancy': custom_hourly[hour]})
        elif hour < current_hour:
            base_occupancy = params['hourly_peak'] * (1.0 - abs(hour - 14) / 6.0 * 0.5)
            today_hourly.append({'hour': hour, 'occupancy': min(1.0, max(0.1, base_occupancy))})
        elif hour == current_hour:
            today_hourly.append({'hour': hour, 'occupancy': occupancy})
        else:
            base_occupancy = params['hourly_peak'] * (1.0 - abs(hour - 14) / 6.0 * 0.5)
            today_hourly.append({'hour': hour, 'occupancy': min(1.0, max(0.1, base_occupancy))})
    
    # Weekly pattern with custom peak
    week_same_time = [
        {'day': 'Mon', 'occupancy': params['weekly_peak'] * 0.9},
        {'day': 'Tue', 'occupancy': params['weekly_peak'] * 0.85},
        {'day': 'Wed', 'occupancy': params['weekly_peak']},
        {'day': 'Thu', 'occupancy': params['weekly_peak'] * 0.95},
        {'day': 'Fri', 'occupancy': params['weekly_peak'] * 1.0},
        {'day': 'Sat', 'occupancy': params['weekly_peak'] * 0.75},
        {'day': 'Sun', 'occupancy': params['weekly_peak'] * 0.5}
    ]
    
    # Generate alternatives based on count
    alternatives = []
    alt_names = ['Court B', 'Court C', 'Court D']
    alt_statuses = ['light', 'normal', 'busy']
    for i in range(min(params['alternatives'], 3)):
        alternatives.append({
            'id': f'basketball_{chr(98+i)}',  # b, c, d
            'name': alt_names[i],
            'distance_m': 200 + (i * 300),
            'occupancy': 0.2 + (i * 0.15),
            'people': i + 2,
            'status': alt_statuses[i % len(alt_statuses)]
        })
    
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
            'uv_index': params['uv'],
            'voc_level': params.get('air_quality', 'good'),  # Use custom air quality if provided
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
            'surface': params.get('surface', 'Concrete'),  # Use custom surface if provided
            'lighting_hours': params.get('lighting_hours', '6AM-10PM'),  # Use custom lighting if provided
            'rating_avg': params['rating'],
            'rating_count': 47,
            'last_cleaned': params.get('last_cleaned', 'Today'),  # Use custom last_cleaned if provided
            'size': params.get('size', 'Full court'),  # Use custom size if provided
            'capacity': params.get('capacity', 10),  # Use custom capacity if provided
            'facilities': params.get('facilities', ['Water', 'Seating', 'Restroom', 'Parking'])  # Use custom facilities if provided
        }
    }

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/current_data')
def api_current_data():
    """API endpoint to get current crowd data"""
    return json.dumps(current_crowd_data)

# ========== SOCKET.IO EVENTS ==========

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Client disconnected: {request.sid}')

@socketio.on('send_test_data_module5')
def handle_send_test_data_module5(data):
    """Send simulated test data to Module 5 (triggered from dashboard)"""
    court_id = data.get('court_id', 'basketball_a')
    test_scenario = data.get('scenario', 'normal')  # 'normal', 'full', 'empty', 'busy', 'custom'
    custom_data = data.get('custom_data', None)  # Optional custom overrides
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Sending test data to Module 5: {test_scenario}')
    if custom_data:
        print(f'  Custom overrides: {custom_data}')
    
    # Generate test data based on scenario
    test_data = generate_module5_test_data(court_id, test_scenario, custom_data)
    
    # Send to Module 5
    socketio.emit('DisplayUpdate', test_data)
    
    return {'status': 'success', 'scenario': test_scenario}

@socketio.on('button_press_debug')
def handle_button_press_debug(data):
    """Handle button press debug info from Module 5"""
    module_id = data.get('module_id', 'unknown')
    button_id = data.get('button_id', 0)
    button_name = data.get('button_name', 'T?')
    view = data.get('view', 'unknown')
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    # Log to console
    print(f'[{datetime.now().strftime("%H:%M:%S")}] [MODULE5 DEBUG] Button {button_id} ({button_name}) pressed on {module_id} -> View: {view}')
    
    # Broadcast to all connected dashboard clients
    socketio.emit('ButtonPressDebug', {
        'module_id': module_id,
        'button_id': button_id,
        'button_name': button_name,
        'view': view,
        'timestamp': timestamp
    })

@socketio.on('module_register')
def handle_module_register(data):
    """Register a module when it connects"""
    module_type = data.get('module_type')
    module_id = data.get('module_id')
    
    if module_type in connected_modules:
        if module_id not in connected_modules[module_type]:
            connected_modules[module_type].append(module_id)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module registered: {module_id} ({module_type})')
    emit('registration_ack', {'status': 'success', 'module_id': module_id})

@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video_frame(data):
    """Handle video frame from Module 1 - Process with Google AI API"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Video frame received from {data.get("module_id")}')
    
    try:
        # Extract video frame (base64 encoded JPEG)
        frame_base64 = data['data'].get('video_frame')
        if not frame_base64:
            print("[ERROR] No video frame in data")
            return
        
        # Decode base64 to image bytes
        image_bytes = base64.b64decode(frame_base64)
        print(f"[DEBUG] Decoded image: {len(image_bytes)} bytes")
        
        # Process with Google AI API to count people (if API key is set)
        people_count = process_image_with_google_ai(image_bytes)
        ai_enabled = bool(GOOGLE_AI_API_KEY)
        
        # Get sensor data from Module 1
        noise_db = data['data'].get('noise_db', 0)
        motion_detected = data['data'].get('motion_detected', False)
        proximity_triggered = data['data'].get('proximity_triggered', False)
        
        # Calculate confidence and crowd level
        confidence = calculate_confidence(people_count, noise_db, motion_detected, proximity_triggered)
        crowd_level = determine_crowd_level(people_count)
        
        # Create processed crowd data
        processed_crowd_data = {
            'module_id': data.get('module_id'),
            'court_id': data.get('court_id'),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'data': {
                'people_count': people_count,
                'crowd_level': crowd_level,
                'noise_db': noise_db,
                'motion_detected': motion_detected,
                'proximity_triggered': proximity_triggered,
                'confidence': round(confidence, 2),
                'ai_enabled': ai_enabled,
                'sensors_status': data['data'].get('sensors_status', {})
            }
        }
        
        # Update current data
        global current_crowd_data
        current_crowd_data = processed_crowd_data['data']
        current_crowd_data['timestamp'] = processed_crowd_data['timestamp']
        
        # Store processed data
        crowd_data_history.append(processed_crowd_data)
        if len(crowd_data_history) > 100:  # Keep last 100 entries
            crowd_data_history.pop(0)
        
        # Broadcast video frame to dashboard (always, even without API key)
        print(f"[DEBUG] Broadcasting video frame to dashboard ({len(frame_base64)} bytes)")
        socketio.emit('VideoFrameUpdate', {
            'video_frame': frame_base64,  # Send original base64 frame
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        })
        
        # Broadcast processed crowd data to all connected web clients (dashboard)
        socketio.emit('CrowdDataUpdate', processed_crowd_data)
        
        # Also send to Module 4 (Dashboard) and Module 5 (Display) if they're connected
        socketio.emit('DashboardUpdate', {
            'type': 'crowd_update',
            'data': processed_crowd_data,
            'alerts': []  # Could add alert processing here
        })
        
        # Send complete Module 5 data
        display_data = generate_module5_data(data.get('court_id'), people_count, crowd_level, confidence)
        socketio.emit('DisplayUpdate', display_data)
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Processed: {people_count} people, '
              f'{crowd_level}, confidence={confidence:.2f}, noise={noise_db}dB')
        
    except Exception as e:
        print(f'[ERROR] Error processing video frame: {e}')
        import traceback
        traceback.print_exc()

# ========== SERVER STARTUP ==========

if __name__ == '__main__':
    print("=" * 60)
    print("Smart Sports Facility System - Cloud Server")
    print("=" * 60)
    print(f"Server IP: {SERVER_IP}")
    print(f"Server Port: {SERVER_PORT}")
    print(f"Google AI API Key: {'Set' if GOOGLE_AI_API_KEY else 'NOT SET (using fallback)'}")
    print("=" * 60)
    print("Starting server...")
    print(f"Dashboard available at: http://{SERVER_IP}:{SERVER_PORT}")
    print("=" * 60)
    
    # Check if Google AI API key is set
    if not GOOGLE_AI_API_KEY:
        print("\n[WARNING] Google AI API key not set!")
        print("Set it as environment variable: export GOOGLE_AI_API_KEY='your-key'")
        print("Or install google-generativeai: pip install google-generativeai")
        print("Server will run but people counting will not work.\n")
    
    try:
        wsgi.server(eventlet.listen((SERVER_IP, SERVER_PORT)), app)
    except OSError as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        print("Make sure:")
        print("1. The IP address is correct")
        print("2. Port 5000 is not already in use")
        print("3. You have permission to bind to that address")

