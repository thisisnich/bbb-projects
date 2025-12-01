# 📡 DATA TRANSMISSION PROTOCOL
## Smart Sports Facility System - Communication Specification

**Based on:** Flask-SocketIO pattern from ConnectedSystemClassroom  
**Protocol:** WebSocket (Socket.IO) over HTTP  
**Format:** JSON

---

## 🔧 TECHNICAL STACK

### Server (Cloud/Module 4)
- **Framework:** Flask with Flask-SocketIO
- **Async Mode:** Eventlet
- **Port:** 5000 (configurable)
- **Dependencies:**
  ```python
  flask>=2.0.0
  flask-socketio>=5.0.0
  eventlet>=0.33.0
  ```

### Clients (Modules 1, 2, 3, 5)
- **Library:** python-socketio (Client)
- **Installation:**
  ```bash
  sudo pip3 install python-socketio
  ```

---

## 🌐 NETWORK ARCHITECTURE

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  MODULE 1   │────────▶│             │◀────────│  MODULE 2   │
│   (Crowd)   │ SocketIO │   CLOUD     │ SocketIO │  (Environment)│
└─────────────┘         │   SERVER    │         └─────────────┘
                        │  (Module 4) │
┌─────────────┐         │             │         ┌─────────────┐
│  MODULE 3   │────────▶│             │◀────────│  MODULE 5   │
│  (Feedback) │ SocketIO │             │ SocketIO │  (Display)  │
└─────────────┘         └─────────────┘         └─────────────┘
```

**All modules connect to the same server URL:**
```python
SERVER_URL = 'http://192.168.X.X:5000'  # Replace with server IP
```

---

## 📤 MODULE 1: CROWD INTELLIGENCE UNIT

**IMPORTANT:** Module 1 sends **VIDEO FRAMES** to the server. The server processes video with Google AI API to count people. Module 1 does NOT count people locally.

### Connection Setup
```python
import socketio
import cv2
import base64
import threading
from datetime import datetime

sio = socketio.Client()
SERVER_URL = 'http://192.168.X.X:5000'  # Cloud server IP

# Webcam setup
webcam_cap = None
WEBCAM_FPS = 2  # Send 2 frames per second (every 0.5 seconds)

@sio.event
def connect():
    print(f'[{datetime.now()}] Module 1 connected to server')
    # Register this module
    sio.emit('module_register', {
        'module_id': 'crowd_unit_1',
        'module_type': 'crowd_detection',
        'court_id': 'basketball_a',
        'timestamp': datetime.now().isoformat()
    })

sio.connect(SERVER_URL)
```

### Video Frame Transmission (Every 0.5 seconds)

**Event Name:** `CrowdVideoFrameEvent`

**Data Format:**
```python
sio.emit('CrowdVideoFrameEvent', {
    'module_id': 'crowd_unit_1',
    'court_id': 'basketball_a',
    'timestamp': '2025-11-17T15:30:00',
    'data': {
        'video_frame': 'base64_encoded_jpeg_string',  # Base64 encoded JPEG image
        'noise_db': 75,  # From MIC Click
        'motion_detected': True,  # From Motion Click
        'proximity_triggered': True,  # From Proximity Click
        'sensors_status': {
            'webcam': 'ok',
            'mic': 'ok',
            'motion': 'ok',
            'proximity': 'ok'
        }
    }
})
```

**Example Implementation:**
```python
import time
import cv2
import base64

def init_webcam():
    """Initialize USB webcam"""
    global webcam_cap
    try:
        webcam_cap = cv2.VideoCapture(0)  # /dev/video0
        if webcam_cap.isOpened():
            webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            webcam_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            print("[WEBCAM] Camera initialized")
            return True
    except Exception as e:
        print(f"[WEBCAM] Error initializing: {e}")
    return False

def capture_and_encode_frame():
    """Capture frame from webcam and encode as base64 JPEG"""
    global webcam_cap
    try:
        if webcam_cap is None or not webcam_cap.isOpened():
            if not init_webcam():
                return None
        
        ret, frame = webcam_cap.read()
        if not ret or frame is None:
            return None
        
        # Encode frame as JPEG (85% quality for smaller size)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        ret, jpeg_bytes = cv2.imencode('.jpg', frame, encode_param)
        
        if ret and jpeg_bytes is not None:
            # Encode as base64 for transmission
            frame_base64 = base64.b64encode(jpeg_bytes.tobytes()).decode('utf-8')
            return frame_base64
    except Exception as e:
        print(f'[WEBCAM] Frame capture error: {e}')
    return None

def send_video_frames():
    """Send video frames continuously to server"""
    frame_interval = 1.0 / WEBCAM_FPS  # 0.5 seconds
    
    while True:
        try:
            if sio.connected:
                # Capture and encode frame
                frame_base64 = capture_and_encode_frame()
                
                if frame_base64:
                    # Read other sensors
                    noise_level = read_mic_click()
                    motion = read_motion_click()
                    proximity = read_proximity_click()
                    
                    # Send video frame with sensor data
                    sio.emit('CrowdVideoFrameEvent', {
                        'module_id': 'crowd_unit_1',
                        'court_id': 'basketball_a',
                        'timestamp': datetime.now().isoformat(),
                        'data': {
                            'video_frame': frame_base64,
                            'noise_db': noise_level,
                            'motion_detected': motion,
                            'proximity_triggered': proximity,
                            'sensors_status': {
                                'webcam': 'ok',
                                'mic': 'ok',
                                'motion': 'ok',
                                'proximity': 'ok'
                            }
                        }
                    })
                    
                    print(f"[{datetime.now()}] Video frame sent ({len(frame_base64)} bytes)")
            
        except Exception as e:
            print(f"Error sending video frame: {e}")
        
        time.sleep(frame_interval)

# Initialize webcam
if init_webcam():
    # Start video streaming in separate thread
    video_thread = threading.Thread(target=send_video_frames, daemon=True)
    video_thread.start()
```

---

## 📤 MODULE 2: ENVIRONMENTAL CONDITIONS STATION

### Connection Setup
```python
import socketio
from datetime import datetime

sio = socketio.Client()
SERVER_URL = 'http://192.168.X.X:5000'

@sio.event
def connect():
    print(f'[{datetime.now()}] Module 2 connected to server')
    sio.emit('module_register', {
        'module_id': 'environment_unit_2',
        'module_type': 'environment',
        'timestamp': datetime.now().isoformat()
    })

sio.connect(SERVER_URL)
```

### Data Transmission (Every 30 seconds)

**Event Name:** `EnvironmentDataEvent`

**Data Format:**
```python
sio.emit('EnvironmentDataEvent', {
    'module_id': 'environment_unit_2',
    'timestamp': '2025-11-17T15:30:00',
    'data': {
        'temperature_c': 32,
        'humidity_percent': 78,
        'pressure_hpa': 1013,
        'voc_level': 'good',  # 'good', 'moderate', 'poor'
        'voc_reading': 245,
        'uv_index': 9,
        'comfort_score': 3.0,  # 1.0 to 5.0
        'playable': True,
        'warnings': ['high_uv', 'high_heat'],
        'recommendations': ['use_sunscreen', 'stay_hydrated', 'play_after_6pm']
    }
})
```

**Example Implementation:**
```python
def send_environment_data():
    """Send environment data every 30 seconds"""
    while True:
        try:
            # Read sensors
            temp = read_environment_click_temperature()
            humidity = read_environment_click_humidity()
            pressure = read_environment_click_pressure()
            voc = read_environment_click_voc()
            uv = read_uv3_click()
            
            # Calculate comfort score
            comfort_score = calculate_comfort_score(temp, humidity, uv, voc)
            warnings = generate_warnings(temp, uv, voc)
            recommendations = generate_recommendations(temp, uv, comfort_score)
            
            # Send to server
            sio.emit('EnvironmentDataEvent', {
                'module_id': 'environment_unit_2',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'temperature_c': temp,
                    'humidity_percent': humidity,
                    'pressure_hpa': pressure,
                    'voc_level': classify_voc(voc),
                    'voc_reading': voc,
                    'uv_index': uv,
                    'comfort_score': comfort_score,
                    'playable': comfort_score >= 2.0,
                    'warnings': warnings,
                    'recommendations': recommendations
                }
            })
            
            print(f"[{datetime.now()}] Environment data sent: {temp}°C, UV={uv}")
            
        except Exception as e:
            print(f"Error sending environment data: {e}")
        
        time.sleep(30)
```

---

## 📤 MODULE 3: INTERACTIVE FEEDBACK KIOSK

**IMPORTANT:** Module 3 supports multiple questions. Each question can be either:
- **Rating type:** User selects a rating (1-5 stars, or custom scale)
- **Text type:** User provides text feedback/report

User selects ONE question and submits rating/text for that question only.

### Connection Setup
```python
import socketio
from datetime import datetime

sio = socketio.Client()
SERVER_URL = 'http://192.168.X.X:5000'

@sio.event
def connect():
    print(f'[{datetime.now()}] Module 3 connected to server')
    sio.emit('module_register', {
        'module_id': 'feedback_kiosk_3',
        'module_type': 'feedback',
        'court_id': 'basketball_a',
        'timestamp': datetime.now().isoformat()
    })

sio.connect(SERVER_URL)
```

### Data Transmission (Event-Driven - When User Interacts)

**Event Name:** `FeedbackDataEvent`

**Rating Submission (for a specific question):**
```python
sio.emit('FeedbackDataEvent', {
    'module_id': 'feedback_kiosk_3',
    'court_id': 'basketball_a',
    'timestamp': '2025-11-17T15:32:45',
    'data': {
        'report_type': 'rating',  # 'rating' or 'text'
        'question_id': 'overall_quality',  # ID of the question answered
        'question_text': 'How would you rate the overall court quality?',  # Optional: question text
        'rating': 4,  # Rating value (1-5, or custom scale)
        'rating_scale': '1-5',  # Scale used: '1-5', '1-10', 'yes-no', etc.
        'interaction_time_seconds': 8,
        'gesture_used': True
    }
})
```

**Text Report Submission (for a specific question):**
```python
sio.emit('FeedbackDataEvent', {
    'module_id': 'feedback_kiosk_3',
    'court_id': 'basketball_a',
    'timestamp': '2025-11-17T15:35:12',
    'data': {
        'report_type': 'text',  # 'rating' or 'text'
        'question_id': 'maintenance_issue',  # ID of the question answered
        'question_text': 'Report a maintenance issue',  # Optional: question text
        'text_response': 'Net is broken on the north side',  # User's text input
        'issue_category': 'net_broken',  # Optional: categorized issue type
        'qr_code_generated': 'https://report.courts.sg/issue/A3F7',  # If applicable
        'priority': 'medium',  # 'low', 'medium', 'high' (if applicable)
        'interaction_time_seconds': 12,
        'gesture_used': True
    }
})
```

**Example Question Configuration:**
```python
# Example questions that Module 3 might display
FEEDBACK_QUESTIONS = [
    {
        'id': 'overall_quality',
        'text': 'How would you rate the overall court quality?',
        'type': 'rating',  # 'rating' or 'text'
        'rating_scale': '1-5',  # For rating type
        'options': ['1', '2', '3', '4', '5']  # Rating options
    },
    {
        'id': 'court_cleanliness',
        'text': 'How clean is the court?',
        'type': 'rating',
        'rating_scale': '1-5',
        'options': ['1', '2', '3', '4', '5']
    },
    {
        'id': 'maintenance_issue',
        'text': 'Report a maintenance issue',
        'type': 'text',  # Text input
        'categories': ['net_broken', 'floor_damaged', 'lights_not_working', 'needs_cleaning']
    },
    {
        'id': 'safety_concern',
        'text': 'Report a safety concern',
        'type': 'text',
        'categories': ['slippery_floor', 'broken_equipment', 'poor_lighting', 'other']
    }
]
```

**Example Implementation:**
```python
import time

def handle_rating_submission(question_id, question_text, rating_value, rating_scale='1-5'):
    """Send rating when user confirms selection for a specific question"""
    try:
        start_time = time.time()
        # ... gesture interaction happens ...
        interaction_time = time.time() - start_time
        
        sio.emit('FeedbackDataEvent', {
            'module_id': 'feedback_kiosk_3',
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'rating',
                'question_id': question_id,
                'question_text': question_text,
                'rating': rating_value,
                'rating_scale': rating_scale,
                'interaction_time_seconds': int(interaction_time),
                'gesture_used': True
            }
        })
        
        print(f"[{datetime.now()}] Rating submitted: {question_id} = {rating_value}")
        
    except Exception as e:
        print(f"Error sending rating: {e}")

def handle_text_submission(question_id, question_text, text_response, issue_category=None):
    """Send text feedback when user submits text for a specific question"""
    try:
        start_time = time.time()
        # ... gesture interaction happens ...
        interaction_time = time.time() - start_time
        
        # Generate QR code if it's a maintenance issue
        qr_code = None
        priority = 'low'
        if issue_category:
            qr_code = generate_qr_code_url(issue_category)
            priority = determine_priority(issue_category)
        
        sio.emit('FeedbackDataEvent', {
            'module_id': 'feedback_kiosk_3',
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'text',
                'question_id': question_id,
                'question_text': question_text,
                'text_response': text_response,
                'issue_category': issue_category,
                'qr_code_generated': qr_code,
                'priority': priority,
                'interaction_time_seconds': int(interaction_time),
                'gesture_used': True
            }
        })
        
        print(f"[{datetime.now()}] Text feedback submitted: {question_id} = {text_response[:50]}...")
        
    except Exception as e:
        print(f"Error sending text feedback: {e}")

# Example usage:
# User selects "overall_quality" question and rates it 4 stars
handle_rating_submission(
    question_id='overall_quality',
    question_text='How would you rate the overall court quality?',
    rating_value=4,
    rating_scale='1-5'
)

# User selects "maintenance_issue" question and types text
handle_text_submission(
    question_id='maintenance_issue',
    question_text='Report a maintenance issue',
    text_response='Net is broken on the north side',
    issue_category='net_broken'
)
```

---

## 📥 MODULE 4: SECURITY & MAINTENANCE ALERT DASHBOARD

### Server-Side Event Handlers

**Receive from Module 1 (Crowd):**
```python
@socketio.event
def CrowdDataEvent(data):
    """Handle crowd detection data from Module 1"""
    print(f'[{datetime.now()}] Crowd data received: {data}')
    
    # Store in database
    store_crowd_data(data)
    
    # Process for alerts
    check_unusual_activity(data)
    
    # Broadcast to Module 4 dashboard
    socketio.emit('DashboardUpdate', {
        'type': 'crowd_update',
        'data': data
    })
```

**Receive from Module 2 (Environment):**
```python
@socketio.event
def EnvironmentDataEvent(data):
    """Handle environment data from Module 2"""
    print(f'[{datetime.now()}] Environment data received: {data}')
    
    # Store in database
    store_environment_data(data)
    
    # Check for environmental hazards
    check_environmental_hazards(data)
    
    # Broadcast to Module 4 dashboard
    socketio.emit('DashboardUpdate', {
        'type': 'environment_update',
        'data': data
    })
```

**Receive from Module 3 (Feedback):**
```python
@socketio.event
def FeedbackDataEvent(data):
    """Handle feedback data from Module 3"""
    print(f'[{datetime.now()}] Feedback data received: {data}')
    
    # Store in database
    store_feedback_data(data)
    
    # Check for low ratings or maintenance issues
    if data['data']['type'] == 'rating' and data['data']['rating'] <= 2:
        trigger_low_rating_alert(data)
    elif data['data']['type'] == 'maintenance':
        trigger_maintenance_alert(data)
    
    # Broadcast to Module 4 dashboard
    socketio.emit('DashboardUpdate', {
        'type': 'feedback_update',
        'data': data
    })
```

### Module 4 Client (Receives Processed Data)

**Connection:**
```python
import socketio

sio = socketio.Client()
SERVER_URL = 'http://192.168.X.X:5000'

@sio.event
def connect():
    print(f'[{datetime.now()}] Module 4 (Dashboard) connected to server')
    sio.emit('module_register', {
        'module_id': 'security_dashboard_4',
        'module_type': 'dashboard',
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def DashboardUpdate(data):
    """Receive dashboard updates from server"""
    print(f'[{datetime.now()}] Dashboard update received: {data["type"]}')
    
    # Update OLED display
    if data['type'] == 'alert':
        display_alert(data['data'])
        trigger_buzz(data['data']['severity'])
    elif data['type'] == 'crowd_update':
        update_crowd_status(data['data'])
    elif data['type'] == 'environment_update':
        update_environment_status(data['data'])
    elif data['type'] == 'feedback_update':
        update_feedback_status(data['data'])

sio.connect(SERVER_URL)
```

**Receive Alert Data:**
```python
@sio.event
def AlertEvent(alert_data):
    """Receive alerts from server"""
    print(f'[{datetime.now()}] Alert received: {alert_data["type"]}')
    
    # Update displays
    update_7segment_display(len(alert_data['alerts']))
    update_led_matrix(alert_data['highest_severity'])
    display_alert_on_oled(alert_data)
    trigger_audio_alert(alert_data['type'], alert_data['severity'])
```

---

## 📥 MODULE 5: SMART COURT INFORMATION DISPLAY

### Module 5 Client (Receives Processed Data)

**Connection:**
```python
import socketio

sio = socketio.Client()
SERVER_URL = 'http://192.168.X.X:5000'

@sio.event
def connect():
    print(f'[{datetime.now()}] Module 5 (Display) connected to server')
    sio.emit('module_register', {
        'module_id': 'court_display_5_a',
        'module_type': 'display',
        'court_id': 'basketball_a',
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def DisplayUpdate(data):
    """Receive display updates from server"""
    print(f'[{datetime.now()}] Display update received for {data["court_id"]}')
    
    # Update OLED display based on current view
    if current_view == 'status':
        show_current_status(data)
    elif current_view == 'history':
        show_history(data)
    elif current_view == 'weather':
        show_weather(data)
    elif current_view == 'alternatives':
        show_alternatives(data)
    
    # Update bar graph
    update_bar_graph(data['patterns']['today_hourly'])

sio.connect(SERVER_URL)
```

**Receive Court Data:**
```python
@sio.event
def CourtDataEvent(court_data):
    """Receive processed court data from server"""
    print(f'[{datetime.now()}] Court data received: {court_data["court_id"]}')
    
    # Update all displays
    update_oled_display(court_data)
    update_bar_graph(court_data['patterns'])
    
    # Store for local use
    current_court_data = court_data
```

---

## 🖥️ CLOUD SERVER IMPLEMENTATION

### Complete Server Code Structure

```python
from flask import Flask
from flask_socketio import SocketIO, emit
from datetime import datetime
import eventlet
from eventlet import wsgi

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Track connected modules
connected_modules = {
    'crowd': [],
    'environment': [],
    'feedback': [],
    'dashboard': [],
    'display': []
}

# Data storage (in production, use database)
crowd_data_history = []
environment_data_history = []
feedback_data_history = []

@app.route('/')
def index():
    return "Smart Sports Facility System - Cloud Server"

# ========== MODULE REGISTRATION ==========

@socketio.on('module_register')
def handle_module_register(data):
    """Register a module when it connects"""
    module_type = data.get('module_type')
    module_id = data.get('module_id')
    
    if module_type in connected_modules:
        if module_id not in connected_modules[module_type]:
            connected_modules[module_type].append(module_id)
    
    print(f'[{datetime.now()}] Module registered: {module_id} ({module_type})')
    emit('registration_ack', {'status': 'success', 'module_id': module_id})

# ========== RECEIVE DATA FROM MODULES 1-3 ==========

@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video_frame(data):
    """Receive video frame from Module 1 - Process with Google AI API"""
    print(f'[{datetime.now()}] Video frame received from {data.get("module_id")}')
    
    try:
        # Extract video frame (base64 encoded JPEG)
        frame_base64 = data['data'].get('video_frame')
        if not frame_base64:
            return
        
        # Decode base64 to image bytes
        import base64
        image_bytes = base64.b64decode(frame_base64)
        
        # Process with Google AI API to count people
        people_count = process_image_with_google_ai(image_bytes)
        
        # Get sensor data from Module 1
        noise_db = data['data'].get('noise_db', 0)
        motion_detected = data['data'].get('motion_detected', False)
        proximity_triggered = data['data'].get('proximity_triggered', False)
        
        # Calculate confidence and crowd level
        confidence = calculate_confidence(people_count, noise_db, motion_detected, proximity_triggered)
        crowd_level = determine_crowd_level(people_count, confidence)
        
        # Create processed crowd data
        processed_crowd_data = {
            'module_id': data.get('module_id'),
            'court_id': data.get('court_id'),
            'timestamp': data.get('timestamp'),
            'data': {
                'people_count': people_count,
                'crowd_level': crowd_level,
                'noise_db': noise_db,
                'motion_detected': motion_detected,
                'proximity_triggered': proximity_triggered,
                'confidence': confidence,
                'sensors_status': data['data'].get('sensors_status', {})
            }
        }
        
        # Store processed data
        crowd_data_history.append(processed_crowd_data)
        
        # Process for alerts
        alerts = process_crowd_data_for_alerts(processed_crowd_data)
        
        # Send to Module 4 (Dashboard)
        socketio.emit('DashboardUpdate', {
            'type': 'crowd_update',
            'data': processed_crowd_data,
            'alerts': alerts
        })
        
        # Process and send to Module 5 (Display)
        processed_data = process_for_display(processed_crowd_data)
        socketio.emit('DisplayUpdate', processed_data)
        
        print(f'[{datetime.now()}] Processed: {people_count} people, {crowd_level}, confidence={confidence:.2f}')
        
    except Exception as e:
        print(f'Error processing video frame: {e}')

def process_image_with_google_ai(image_bytes):
    """Process image with Google AI API to count people"""
    try:
        import google.generativeai as genai
        
        # Configure API key (set as environment variable)
        genai.configure(api_key=os.getenv('GOOGLE_AI_API_KEY'))
        
        # Use Gemini Vision API
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Create prompt
        prompt = "Count the number of people visible in this image. Return only the number."
        
        # Process image
        response = model.generate_content([prompt, {
            'mime_type': 'image/jpeg',
            'data': image_bytes
        }])
        
        # Extract number from response
        people_count = int(response.text.strip())
        return max(0, people_count)  # Ensure non-negative
        
    except Exception as e:
        print(f'Google AI API error: {e}')
        return 0  # Return 0 if processing fails

@socketio.on('EnvironmentDataEvent')
def handle_environment_data(data):
    """Receive environment data from Module 2"""
    print(f'[{datetime.now()}] Environment data received from {data.get("module_id")}')
    
    # Store data
    environment_data_history.append(data)
    
    # Process for alerts
    alerts = process_environment_data_for_alerts(data)
    
    # Send to Module 4 (Dashboard)
    socketio.emit('DashboardUpdate', {
        'type': 'environment_update',
        'data': data,
        'alerts': alerts
    })
    
    # Send to Module 5 (Display) - weather info
    socketio.emit('DisplayUpdate', {
        'type': 'weather_update',
        'data': data['data']
    })

@socketio.on('FeedbackDataEvent')
def handle_feedback_data(data):
    """Receive feedback data from Module 3"""
    print(f'[{datetime.now()}] Feedback data received from {data.get("module_id")}')
    
    # Store data
    feedback_data_history.append(data)
    
    # Process for alerts based on report_type
    alerts = []
    report_type = data['data'].get('report_type')  # 'rating' or 'text'
    
    if report_type == 'rating':
        # Check for low ratings
        rating = data['data'].get('rating', 0)
        if rating <= 2:  # Low rating (1 or 2 stars)
            alerts.append(create_low_rating_alert(data))
    elif report_type == 'text':
        # Check if it's a maintenance issue
        issue_category = data['data'].get('issue_category')
        if issue_category:
            alerts.append(create_maintenance_alert(data))
    
    # Send to Module 4 (Dashboard)
    if alerts:
        socketio.emit('AlertEvent', {
            'alerts': alerts,
            'highest_severity': max([a['severity'] for a in alerts])
        })
    
    # Update ratings for Module 5 (Display)
    if report_type == 'rating':
        update_court_ratings(data)

# ========== PROCESSING FUNCTIONS ==========

def process_crowd_data_for_alerts(data):
    """Check crowd data for alert conditions"""
    alerts = []
    current_time = datetime.now()
    
    # Check for unusual activity (late night)
    if (current_time.hour >= 22 or current_time.hour <= 6) and data['data']['people_count'] > 0:
        alerts.append({
            'id': f"alert_{datetime.now().timestamp()}",
            'type': 'unusual_activity',
            'court_id': data.get('court_id'),
            'severity': 'high',
            'data': data['data'],
            'action_required': 'Security check recommended'
        })
    
    # Check for noise complaints
    if (current_time.hour >= 22 or current_time.hour <= 7) and data['data']['noise_db'] > 75:
        alerts.append({
            'id': f"alert_{datetime.now().timestamp()}",
            'type': 'noise_complaint',
            'court_id': data.get('court_id'),
            'severity': 'high',
            'data': data['data'],
            'action_required': 'Check if disturbing residents'
        })
    
    return alerts

def process_environment_data_for_alerts(data):
    """Check environment data for alert conditions"""
    alerts = []
    
    # Check for extreme heat
    if data['data']['temperature_c'] > 37:
        alerts.append({
            'id': f"alert_{datetime.now().timestamp()}",
            'type': 'environmental_hazard',
            'severity': 'medium',
            'data': data['data'],
            'action_required': 'Post warning signs, check water coolers'
        })
    
    return alerts

def process_for_display(crowd_data):
    """Process crowd data for Module 5 display"""
    # Combine with historical data, generate predictions, etc.
    return {
        'court_id': crowd_data.get('court_id'),
        'current': {
            'occupancy': calculate_occupancy(crowd_data['data']['people_count']),
            'people_count': crowd_data['data']['people_count'],
            'crowd_level': crowd_data['data']['crowd_level'],
            'estimated_wait_min': estimate_wait_time(crowd_data['data']),
            'confidence': crowd_data['data']['confidence']
        },
        'patterns': {
            'today_hourly': get_today_hourly_pattern(crowd_data.get('court_id')),
            'week_same_time': get_weekly_pattern(crowd_data.get('court_id'))
        },
        'recommendations': {
            'best_times_today': get_best_times_today(crowd_data.get('court_id')),
            'nearby_alternatives': get_nearby_courts(crowd_data.get('court_id'))
        }
    }

def create_low_rating_alert(data):
    """Create alert for low rating"""
    question_id = data['data'].get('question_id', 'unknown')
    rating = data['data'].get('rating', 0)
    return {
        'id': f"alert_{datetime.now().timestamp()}",
        'type': 'low_rating',
        'court_id': data.get('court_id'),
        'severity': 'medium',
        'data': {
            'question_id': question_id,
            'question_text': data['data'].get('question_text', ''),
            'rating': rating
        },
        'action_required': f'Inspection required - Low rating ({rating}) for: {question_id}'
    }

def create_maintenance_alert(data):
    """Create alert for maintenance issue"""
    issue_category = data['data'].get('issue_category', 'unknown')
    text_response = data['data'].get('text_response', '')
    return {
        'id': f"alert_{datetime.now().timestamp()}",
        'type': 'maintenance',
        'court_id': data.get('court_id'),
        'severity': 'high',
        'data': {
            'question_id': data['data'].get('question_id', ''),
            'issue_category': issue_category,
            'text_response': text_response,
            'priority': data['data'].get('priority', 'medium')
        },
        'action_required': f"Repair {issue_category}: {text_response[:50]}"
    }

# ========== SERVER STARTUP ==========

if __name__ == '__main__':
    print("=" * 50)
    print("Smart Sports Facility System - Cloud Server")
    print("=" * 50)
    print("Starting server on port 5000...")
    print("Modules should connect to: http://YOUR_IP:5000")
    print("=" * 50)
    
    # Update with your server IP address
    SERVER_IP = '192.168.X.X'  # CHANGE THIS!
    SERVER_PORT = 5000
    
    wsgi.server(eventlet.listen((SERVER_IP, SERVER_PORT)), app)
```

---

## 📋 DATA FLOW SUMMARY

### Module 1 → Cloud → Module 4 & 5
```
Module 1 (Crowd)
    ↓ emit('CrowdVideoFrameEvent', {video_frame: base64_jpeg, ...})
Cloud Server
    ↓ decode base64 → image bytes
    ↓ process with Google AI API → count people
    ↓ calculate confidence & crowd level
    ↓ store processed data
    ↓ emit('DashboardUpdate', {...})  → Module 4
    ↓ emit('DisplayUpdate', {...})     → Module 5
```

### Module 2 → Cloud → Module 4 & 5
```
Module 2 (Environment)
    ↓ emit('EnvironmentDataEvent', {...})
Cloud Server
    ↓ process & store
    ↓ emit('DashboardUpdate', {...})  → Module 4
    ↓ emit('DisplayUpdate', {...})     → Module 5
```

### Module 3 → Cloud → Module 4
```
Module 3 (Feedback)
    ↓ emit('FeedbackDataEvent', {report_type: 'rating' or 'text', question_id: ..., ...})
Cloud Server
    ↓ process & store
    ↓ check for alerts (low rating or maintenance issue)
    ↓ emit('AlertEvent', {...})        → Module 4
    ↓ update ratings for Module 5 (if rating type)
```

---

## 🔧 CONFIGURATION CHECKLIST

### For Each Module (1, 2, 3, 5):
- [ ] Install `python-socketio`: `sudo pip3 install python-socketio`
- [ ] Update `SERVER_URL` with cloud server IP address
- [ ] Test connection: `sio.connect(SERVER_URL)`
- [ ] Register module: `sio.emit('module_register', {...})`
- [ ] Send data using appropriate event name

### For Cloud Server (Module 4):
- [ ] Install dependencies: `pip install flask flask-socketio eventlet`
- [ ] Update `SERVER_IP` in `WebServer.py`
- [ ] Start server: `python WebServer.py`
- [ ] Verify server is accessible on network
- [ ] Test with client connections

---

## 🧪 TESTING

### Test Module Connection
```python
# Simple test script
import socketio
sio = socketio.Client()

@sio.event
def connect():
    print("Connected!")
    sio.emit('module_register', {'module_id': 'test', 'module_type': 'test'})

sio.connect('http://192.168.X.X:5000')
sio.wait()
```

### Test Data Transmission
```python
# Test sending data
sio.emit('CrowdDataEvent', {
    'module_id': 'test_crowd',
    'court_id': 'test_court',
    'timestamp': '2025-11-17T15:30:00',
    'data': {
        'people_count': 5,
        'crowd_level': 'moderate',
        'noise_db': 60,
        'motion_detected': True,
        'proximity_triggered': False,
        'confidence': 0.85
    }
})
```

---

## 📝 NOTES

1. **IP Address Configuration:** All modules must use the same server IP address
2. **Network:** All devices must be on the same Wi-Fi network
3. **Port:** Default port is 5000, ensure firewall allows this port
4. **Error Handling:** Always wrap `sio.connect()` in try-except for connection errors
5. **Reconnection:** SocketIO client automatically reconnects on disconnect
6. **Data Format:** Always use ISO format for timestamps: `datetime.now().isoformat()`

---

**Last Updated:** 2025-11-17  
**Version:** 1.0

