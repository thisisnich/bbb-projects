from flask import Flask, render_template, request, jsonify
import eventlet
from eventlet import wsgi
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import random
import threading
import time
import base64
import os
import sys
from collections import defaultdict

# AI Image Recognition (Claude API)
ANTHROPIC_AVAILABLE = False
anthropic_client = None
anthropic_api_key = ''

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
    # Get API key from environment variable first, then .env file, then hardcoded fallback
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
    
    # Hardcoded fallback removed for security
    # Set ANTHROPIC_API_KEY environment variable or use .env file
    if not anthropic_api_key:
        print("[WARNING] No API key found. Set ANTHROPIC_API_KEY environment variable or use .env file")
    
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
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# --- Historical Data Storage ---
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

def load_history():
    """Load historical data from JSON file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                # Convert weekly dict keys back to int if needed (JSON stores keys as strings)
                if 'weekly' in data:
                    weekly_fixed = {}
                    for hour_str, days in data['weekly'].items():
                        weekly_fixed[int(hour_str)] = days
                    data['weekly'] = weekly_fixed
                # Convert hourly hour keys to int if needed
                if 'hourly' in data:
                    hourly_fixed = {}
                    for date_str, hours in data['hourly'].items():
                        hourly_fixed[date_str] = {int(h): v for h, v in hours.items()}
                    data['hourly'] = hourly_fixed
                return data
    except Exception as e:
        print(f"[WARNING] Could not load history file: {e}")
        import traceback
        traceback.print_exc()
    
    # Return default structure if file doesn't exist or error
    return {
        'hourly': {},  # {date: {hour: occupancy}}
        'weekly': {}  # {hour: {day: [occupancy_values]}}
    }

def save_history(history_data):
    """Save historical data to JSON file"""
    try:
        # Convert to serializable format
        history_to_save = {
            'hourly': history_data['hourly'],
            'weekly': {str(k): v for k, v in history_data['weekly'].items()}
        }
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history_to_save, f, indent=2)
    except Exception as e:
        print(f"[WARNING] Could not save history file: {e}")

def update_history(occupancy, timestamp=None):
    """Update historical data with new occupancy reading"""
    if timestamp is None:
        timestamp = datetime.now()
    
    history = load_history()
    date_str = timestamp.strftime('%Y-%m-%d')
    hour = timestamp.hour
    day_name = timestamp.strftime('%a')  # Mon, Tue, Wed, etc.
    
    # Update hourly data for today
    if date_str not in history['hourly']:
        history['hourly'][date_str] = {}
    history['hourly'][date_str][hour] = occupancy
    
    # Update weekly pattern (same time, different days)
    if hour not in history['weekly']:
        history['weekly'][hour] = {'Mon': [], 'Tue': [], 'Wed': [], 'Thu': [], 'Fri': [], 'Sat': [], 'Sun': []}
    
    # Add to weekly data for this day/hour (keep last 30 entries per day/hour)
    # Only add if occupancy changed significantly (> 0.05) to avoid duplicate entries
    day_data = history['weekly'][hour][day_name]
    
    # Check if we should add this reading (avoid duplicates from polling)
    should_add = (
        len(day_data) == 0 or  # First reading
        abs(day_data[-1] - occupancy) > 0.05 or  # Significant change (>5%)
        (len(day_data) < 5)  # Always keep at least 5 readings for averaging
    )
    
    if should_add:
        day_data.append(occupancy)
        # Keep last 30 entries per day/hour
        if len(day_data) > 30:
            day_data.pop(0)
    
    save_history(history)
    return history

def get_today_hourly_pattern(history, current_hour, current_occupancy):
    """Get hourly pattern for today from history - ONLY measured data, no projections"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    today_hourly = []
    
    for hour in range(8, 22):  # 8 AM to 10 PM
        if hour < current_hour:
            # Past hours: ONLY use historical data if available (measured data only)
            if date_str in history['hourly'] and hour in history['hourly'][date_str]:
                occupancy = history['hourly'][date_str][hour]
                today_hourly.append({'hour': hour, 'occupancy': min(1.0, max(0.0, occupancy))})
            # If no data, skip this hour (don't show estimates)
        elif hour == current_hour:
            # Current hour: use actual current occupancy (measured)
            today_hourly.append({'hour': hour, 'occupancy': current_occupancy})
        else:
            # Future hours: skip (don't show projections)
            pass
    
    return today_hourly

def get_weekly_pattern(history, current_hour, current_occupancy):
    """Get weekly pattern for same time across different days - ONLY measured data, no projections"""
    week_same_time = []
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    if current_hour in history['weekly']:
        for day in days:
            day_data = history['weekly'][current_hour][day]
            if day_data and len(day_data) > 0:
                # Use average occupancy for this day/hour (measured data only)
                avg_occupancy = sum(day_data) / len(day_data)
                week_same_time.append({'day': day, 'occupancy': min(1.0, max(0.0, avg_occupancy))})
            else:
                # No data for this day - add with null/None occupancy so graph skips it
                # This maintains day order alignment with graph labels
                week_same_time.append({'day': day, 'occupancy': None})
    else:
        # No historical data at all - return all days with None to maintain alignment
        for day in days:
            week_same_time.append({'day': day, 'occupancy': None})
    
    return week_same_time

# Initialize history on startup
historical_data = load_history()
print(f"[INFO] Historical data loaded: {len(historical_data['hourly'])} days, {len(historical_data['weekly'])} hours tracked")

# --- Data Storage ---
connected_modules = {
    'crowd_detection': [],
    'environment': [],
    'feedback': [],
    'display': []  # Module 5 display clients
}

# Track which socket IDs are display modules
display_module_sockets = {}  # {socket_id: module_id}

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
    return render_template('index.html')

@app.route('/module5')
def module5_test():
    return render_template('module5.html')

@app.route('/module3')
def module1_test():
    return render_template('module3.html')

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
                        'text': '''Count people in this basketball court image. 
                        Analyze the scene and return ONLY valid JSON in this exact format:
                        {
                            "count": <number>,
                            "details": "<brief description>",
                            "crowd_level": "<empty|light|normal|busy|full>",
                            "confidence": <0.0-1.0>
                        }
                        Do not include any markdown formatting or code blocks.'''
                    }
                ],
            }],
        )
        
        # Parse response
        response_text = message.content[0].text.strip()
        # Remove markdown code blocks if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")
        
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
            }
        }
        
        # Update current_data with AI analysis results
        current_data['crowd'] = crowd_data
        
        # Update historical data with AI analysis result
        occupancy = min(1.0, people_count / 10.0)
        global historical_data
        historical_data = update_history(occupancy)
        
        # Get historical patterns for graphs
        current_hour = datetime.now().hour
        today_hourly = get_today_hourly_pattern(historical_data, current_hour, occupancy)
        week_same_time = get_weekly_pattern(historical_data, current_hour, occupancy)
        
        # Send ONLY Module 1 (crowd) data to Module 5 as partial update
        # This allows Module 5 to update occupancy without requiring all modules
        partial_module5_data = {
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'current': {
                'occupancy': occupancy,
                'people_count': people_count,
                'crowd_level': crowd_level,
                'estimated_wait_min': {
                    'empty': 0,
                    'light': 5,
                    'normal': 10,
                    'busy': 20,
                    'full': 30
                }.get(crowd_level, 10),
                'confidence': confidence,
                'last_update': 'Just now',
                'source': 'ai_image_analysis'
            },
            'patterns': {
                'today_hourly': today_hourly,
                'week_same_time': week_same_time
            }
        }
        
        # Emit partial Module 5 update (only crowd/occupancy data)
        socketio.emit('DisplayUpdate', partial_module5_data)
        
        # Also emit to dashboard for preview
        socketio.emit('crowd_update', crowd_data)
        
        print(f"[{datetime.now()}] Sent AI analysis to Module 5 (partial update): {people_count} people, {confidence:.2%} confidence, occupancy: {partial_module5_data['current']['occupancy']:.1%}")
        
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
    """API endpoint to get current data state for polling"""
    # Always generate Module 5 data if we have any data from Modules 1-3
    module5_data = None
    if current_data.get('crowd') or current_data.get('environment'):
        module5_data = generate_module5_from_modules(
            court_id='basketball_a',
            crowd_data=current_data.get('crowd'),
            env_data=current_data.get('environment'),
            feedback_data=current_data.get('feedback') if current_data.get('feedback') else None
        )
    
    return jsonify({
        'crowd': current_data.get('crowd'),
        'environment': current_data.get('environment'),
        'feedback': current_data.get('feedback', [])[-1] if current_data.get('feedback') else None,
        'module5': module5_data,
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
        print(f"[{datetime.now()}] Module registered: {module_id} ({module_type})")
        
        # Track display module sockets
        if module_type == 'display':
            display_module_sockets[socket_id] = module_id
        
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
    
    # Update historical data with new reading
    if 'data' in data:
        people_count = data['data'].get('people_count', 0)
        occupancy = min(1.0, people_count / 10.0)
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        global historical_data
        historical_data = update_history(occupancy, timestamp)
    
    socketio.emit('crowd_update', data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data
    court_id = data.get('court_id', 'basketball_a')
    module5_data = generate_module5_from_modules(
        court_id=court_id,
        crowd_data=data,
        env_data=current_data['environment'],
        feedback_data=current_data['feedback'] if current_data['feedback'] else None
    )
    socketio.emit('DisplayUpdate', module5_data)
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
        print(f"[{datetime.now()}] Auto-registered module from video frame: {module_id} ({module_type})")
        
        # Notify dashboard of new connection
        socketio.emit('module_connected', {
            'module_id': module_id,
            'module_type': module_type,
            'timestamp': datetime.now().isoformat()
        })
    
    # Update current data if video frame includes crowd data
    if 'data' in data and data['data']:
        # Merge video frame data with existing crowd data
        if current_data['crowd']:
            current_data['crowd'].update(data)
        else:
            current_data['crowd'] = data
    
    socketio.emit('crowd_video_update', data)

# --- MODULE 2: ENVIRONMENT DATA ---
@socketio.on('EnvironmentDataEvent')
def handle_environment_data(data):
    """Receive environment sensor data from Module 2"""
    print(f"[{datetime.now()}] Received Environment Data: {data}")
    current_data['environment'] = data
    socketio.emit('environment_update', data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data
    court_id = data.get('court_id', 'basketball_a')
    module5_data = generate_module5_from_modules(
        court_id=court_id,
        crowd_data=current_data['crowd'],
        env_data=data,
        feedback_data=current_data['feedback'] if current_data['feedback'] else None
    )
    socketio.emit('DisplayUpdate', module5_data)
    print(f"[{datetime.now()}] Module 5 data generated from Module 2 data and sent to dashboard")

# --- MODULE 3: FEEDBACK DATA ---
@socketio.on('FeedbackStatusEvent')
def handle_feedback_status(data):
    """Receive kiosk status update from Module 3 (on/off based on proximity)"""
    module_id = data.get('module_id', 'unknown')
    is_active = data.get('is_active', False)
    status = 'active' if is_active else 'idle'
    distance = data.get('distance_cm')
    
    print(f"[{datetime.now()}] Module 3 Status: {module_id} is {status}" + 
          (f" (distance: {distance:.1f}cm)" if distance else ""))
    
    # Emit status update to dashboard
    socketio.emit('feedback_status_update', {
        'module_id': module_id,
        'status': status,
        'is_active': is_active,
        'distance_cm': distance,
        'screen_on': is_active,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('FeedbackDataEvent')
def handle_feedback_data(data):
    """Receive feedback data from Module 3"""
    print(f"[{datetime.now()}] Received Feedback Data: {data}")
    # Store feedback in list (keep last 50 entries)
    current_data['feedback'].append(data)
    if len(current_data['feedback']) > 50:
        current_data['feedback'].pop(0)
    
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
    
    # Add calculated statistics to the update
    update_data = data.copy()
    update_data['statistics'] = {
        'average_rating': average_rating,
        'total_ratings': total_ratings,
        'rating_distribution': rating_distribution
    }
    
    socketio.emit('feedback_update', update_data)
    
    # Generate and send Module 5 data based on current Modules 1-3 data
    # (Only update if we have crowd or environment data, otherwise feedback alone isn't enough)
    if current_data['crowd'] or current_data['environment']:
        court_id = data.get('court_id', 'basketball_a')
        module5_data = generate_module5_from_modules(
            court_id=court_id,
            crowd_data=current_data['crowd'],
            env_data=current_data['environment'],
            feedback_data=current_data['feedback'] if current_data['feedback'] else None
        )
        socketio.emit('DisplayUpdate', module5_data)
        print(f"[{datetime.now()}] Module 5 data generated from Module 3 data and sent to dashboard")

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
    
    # Load historical data (don't update here - only update when NEW data arrives)
    global historical_data
    historical_data = load_history()
    
    # Get hourly pattern from actual historical data
    today_hourly = get_today_hourly_pattern(historical_data, current_hour, occupancy)
    
    # Get weekly pattern from actual historical data
    week_same_time = get_weekly_pattern(historical_data, current_hour, occupancy)
    
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
    # Note: socketio.emit() broadcasts by default (no 'to' parameter means all clients)
    socketio.emit('DisplayUpdate', test_data)
    
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
    
    # Store data first
    current_data['crowd'] = crowd_data
    current_data['environment'] = env_data
    current_data['feedback'].append(feedback_data)
    if len(current_data['feedback']) > 50:
        current_data['feedback'].pop(0)
    
    # Emit update events directly to ensure they're broadcast
    socketio.emit('crowd_update', crowd_data)
    socketio.emit('environment_update', env_data)
    socketio.emit('feedback_update', feedback_data)
    
    print(f"[{datetime.now()}] Emitted crowd_update, environment_update, feedback_update events")
    
    # Generate and send Module 5 data
    court_id = 'basketball_a'
    module5_data = generate_module5_from_modules(
        court_id=court_id,
        crowd_data=crowd_data,
        env_data=env_data,
        feedback_data=current_data['feedback'] if current_data['feedback'] else None
    )
    socketio.emit('DisplayUpdate', module5_data)
    
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
        # Remove from connected modules
        if module_id in connected_modules['display']:
            connected_modules['display'].remove(module_id)
        # Remove from socket tracking
        del display_module_sockets[socket_id]
        
        # Emit disconnect event for Module 5
        socketio.emit('module5_display_disconnected', {
            'module_id': module_id,
            'timestamp': datetime.now().isoformat(),
            'count': len(connected_modules['display'])
        })
        print(f"[{datetime.now()}] Module 5 display disconnected: {module_id}")

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

