# 📡 DATA TRANSMISSION - QUICK REFERENCE
## Quick Copy-Paste Code Snippets

---

## 🔌 BASIC CONNECTION TEMPLATE

```python
import socketio
from datetime import datetime
import time

sio = socketio.Client()
SERVER_URL = 'http://192.168.X.X:5000'  # CHANGE THIS!

@sio.event
def connect():
    print(f'[{datetime.now()}] Connected to server')
    sio.emit('module_register', {
        'module_id': 'YOUR_MODULE_ID',
        'module_type': 'YOUR_TYPE',  # 'crowd_detection', 'environment', 'feedback', 'display'
        'court_id': 'basketball_a',  # if applicable
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def disconnect():
    print(f'[{datetime.now()}] Disconnected from server')

# Connect
try:
    sio.connect(SERVER_URL)
except Exception as e:
    print(f"Connection error: {e}")
```

---

## 📤 MODULE 1: CROWD VIDEO FRAMES

**IMPORTANT:** Send VIDEO FRAMES (base64 JPEG), NOT people count. Server processes with AI.

```python
import cv2
import base64

# Capture and encode frame
ret, frame = webcam_cap.read()
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
ret, jpeg_bytes = cv2.imencode('.jpg', frame, encode_param)
frame_base64 = base64.b64encode(jpeg_bytes.tobytes()).decode('utf-8')

# Send video frame (every 0.5 seconds, 2 FPS)
sio.emit('CrowdVideoFrameEvent', {
    'module_id': 'crowd_unit_1',
    'court_id': 'basketball_a',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'video_frame': frame_base64,  # Base64 encoded JPEG
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

---

## 📤 MODULE 2: ENVIRONMENT DATA

```python
# Send every 30 seconds
sio.emit('EnvironmentDataEvent', {
    'module_id': 'environment_unit_2',
    'timestamp': datetime.now().isoformat(),
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

---

## 📤 MODULE 3: FEEDBACK DATA

**IMPORTANT:** Supports multiple questions. Each question can be rating OR text type.

### Rating Submission (for specific question)
```python
sio.emit('FeedbackDataEvent', {
    'module_id': 'feedback_kiosk_3',
    'court_id': 'basketball_a',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'report_type': 'rating',  # 'rating' or 'text'
        'question_id': 'overall_quality',  # ID of question answered
        'question_text': 'How would you rate the overall court quality?',
        'rating': 4,  # Rating value
        'rating_scale': '1-5',  # '1-5', '1-10', etc.
        'interaction_time_seconds': 8,
        'gesture_used': True
    }
})
```

### Text Report (for specific question)
```python
sio.emit('FeedbackDataEvent', {
    'module_id': 'feedback_kiosk_3',
    'court_id': 'basketball_a',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'report_type': 'text',  # 'rating' or 'text'
        'question_id': 'maintenance_issue',  # ID of question answered
        'question_text': 'Report a maintenance issue',
        'text_response': 'Net is broken on the north side',
        'issue_category': 'net_broken',  # Optional category
        'qr_code_generated': 'https://report.courts.sg/issue/A3F7',  # If applicable
        'priority': 'medium',  # 'low', 'medium', 'high'
        'interaction_time_seconds': 12,
        'gesture_used': True
    }
})
```

---

## 📥 MODULE 4: RECEIVE DASHBOARD UPDATES

```python
@sio.event
def DashboardUpdate(data):
    """Receive dashboard updates from server"""
    print(f'Dashboard update: {data["type"]}')
    
    if data['type'] == 'alert':
        # Handle alert
        display_alert(data['data'])
        trigger_buzz(data['data']['severity'])
    elif data['type'] == 'crowd_update':
        update_crowd_status(data['data'])
    elif data['type'] == 'environment_update':
        update_environment_status(data['data'])

@sio.event
def AlertEvent(alert_data):
    """Receive alerts from server"""
    print(f'Alert: {alert_data["type"]}')
    # Update displays, buzzers, etc.
```

---

## 📥 MODULE 5: RECEIVE DISPLAY UPDATES

```python
@sio.event
def DisplayUpdate(data):
    """Receive display updates from server"""
    print(f'Display update for {data.get("court_id")}')
    
    # Update OLED
    if current_view == 'status':
        show_current_status(data)
    elif current_view == 'history':
        show_history(data)
    elif current_view == 'weather':
        show_weather(data)
    
    # Update bar graph
    update_bar_graph(data.get('patterns', {}).get('today_hourly', []))

@sio.event
def CourtDataEvent(court_data):
    """Receive processed court data"""
    update_oled_display(court_data)
    update_bar_graph(court_data.get('patterns', {}))
```

---

## 🖥️ SERVER: EVENT HANDLERS

```python
from flask import Flask
from flask_socketio import SocketIO
import eventlet
from eventlet import wsgi

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

@socketio.on('module_register')
def handle_module_register(data):
    print(f'Module registered: {data.get("module_id")}')
    emit('registration_ack', {'status': 'success'})

@socketio.on('CrowdVideoFrameEvent')
def handle_crowd_video_frame(data):
    """Receive video frame - Process with Google AI API"""
    frame_base64 = data['data'].get('video_frame')
    image_bytes = base64.b64decode(frame_base64)
    
    # Process with Google AI to count people
    people_count = process_image_with_google_ai(image_bytes)
    
    # Create processed data
    processed_data = {
        'module_id': data.get('module_id'),
        'court_id': data.get('court_id'),
        'timestamp': data.get('timestamp'),
        'data': {
            'people_count': people_count,
            'crowd_level': determine_crowd_level(people_count),
            'noise_db': data['data'].get('noise_db'),
            'motion_detected': data['data'].get('motion_detected'),
            'proximity_triggered': data['data'].get('proximity_triggered'),
            'confidence': calculate_confidence(people_count, data['data'])
        }
    }
    
    # Broadcast processed data
    socketio.emit('DashboardUpdate', {'type': 'crowd_update', 'data': processed_data})
    socketio.emit('DisplayUpdate', process_for_display(processed_data))

@socketio.on('EnvironmentDataEvent')
def handle_environment_data(data):
    print(f'Environment data: {data.get("module_id")}')
    socketio.emit('DashboardUpdate', {'type': 'environment_update', 'data': data})
    socketio.emit('DisplayUpdate', {'type': 'weather_update', 'data': data['data']})

@socketio.on('FeedbackDataEvent')
def handle_feedback_data(data):
    print(f'Feedback data: {data.get("module_id")}')
    report_type = data['data'].get('report_type')  # 'rating' or 'text'
    
    # Check for alerts
    if report_type == 'rating' and data['data'].get('rating', 0) <= 2:
        socketio.emit('AlertEvent', create_low_rating_alert(data))
    elif report_type == 'text' and data['data'].get('issue_category'):
        socketio.emit('AlertEvent', create_maintenance_alert(data))

if __name__ == '__main__':
    wsgi.server(eventlet.listen(("192.168.X.X", 5000)), app)
```

---

## 🔧 INSTALLATION

### Client (Modules 1, 2, 3, 5)
```bash
sudo pip3 install python-socketio
```

### Server (Module 4/Cloud)
```bash
pip install flask flask-socketio eventlet
```

---

## ⚙️ CONFIGURATION

1. **Find Server IP:**
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

2. **Update in all files:**
   - Client: `SERVER_URL = 'http://YOUR_IP:5000'`
   - Server: `wsgi.server(eventlet.listen(("YOUR_IP", 5000)), app)`

3. **Test connection:**
   ```python
   sio.connect(SERVER_URL)
   sio.wait()  # Keep connection alive
   ```

---

## 🐛 TROUBLESHOOTING

**Connection Error:**
- Check server is running
- Verify IP address is correct
- Ensure same Wi-Fi network
- Check firewall allows port 5000

**No Data Received:**
- Verify event names match exactly
- Check server console for received events
- Ensure module is registered

**Import Error:**
- Install: `sudo pip3 install python-socketio`
- Check Python version: `python3 --version` (need 3.7+)

---

**See `DATA_TRANSMISSION_PROTOCOL.md` for full documentation.**

