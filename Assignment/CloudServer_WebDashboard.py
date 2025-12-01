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
SERVER_IP = '192.168.72.161'  # CHANGE THIS to your server IP
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
        return 'moderate'
    else:
        return 'full'

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
        
        socketio.emit('DisplayUpdate', {
            'court_id': data.get('court_id'),
            'current': {
                'people_count': people_count,
                'crowd_level': crowd_level,
                'confidence': confidence
            }
        })
        
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

