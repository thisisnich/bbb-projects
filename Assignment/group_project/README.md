# Multi-Module BBBW Development Server

A centralized webserver for receiving and displaying data from multiple BBBW (BeagleBone Black Wireless) modules. Perfect for group development and testing.

## 🎯 Purpose

This server allows group members to:
- Connect their own BBBW devices independently
- Test and debug their modules in real-time
- View data from all modules (Crowd, Environment, Feedback) on one dashboard
- Monitor connection status and activity logs

## 📁 Files

1. **server.py** - Flask/SocketIO web server (runs on PC/Server)
2. **templates/index.html** - Web dashboard displaying all module data
3. **test_client_example.py** - Example client code for testing connections
4. **machine_client.py** - Legacy BeagleBone client (still supported)

## 🚀 Quick Start

### Server Setup (PC/Server)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python server.py
```

The server will start on `http://192.168.68.73:5000`

### Access Dashboard

Open your browser and navigate to:
```
http://192.168.68.73:5000
```

### Test Connection

Run the test client to verify everything works:
```bash
python test_client_example.py
```

### Map page

The **/map** page shows where modules/courts are located. Locations are inferred from each BBB client’s IP when it registers (public IPs are geolocated; private IPs use a default venue position).

- **URL:** `http://<server>:5000/map`
- **Optional env vars** (for private IPs or when geolocation fails):
  - `DEFAULT_MAP_LAT` – default latitude (e.g. `1.3788`)
  - `DEFAULT_MAP_LON` – default longitude (e.g. `103.8489`)

## 📡 Supported Modules

### 1. Crowd Detection Module
**Event:** `CrowdDataEvent`

Sends:
- People count
- Crowd level (empty/light/normal/busy/full)
- Noise level (dB)
- Motion detection status
- Proximity sensor status
- Confidence score

**Example:**
```python
sio.emit('CrowdDataEvent', {
    'module_id': 'crowd_unit_1',
    'court_id': 'basketball_a',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'people_count': 8,
        'crowd_level': 'busy',
        'noise_db': 75,
        'motion_detected': True,
        'proximity_triggered': True,
        'confidence': 0.95
    }
})
```

### 2. Environment Sensors Module
**Event:** `EnvironmentDataEvent`

Sends:
- Temperature (°C)
- Humidity (%)
- Pressure (hPa)
- UV Index
- VOC (air quality)
- Comfort score
- Warnings and recommendations

**Example:**
```python
sio.emit('EnvironmentDataEvent', {
    'module_id': 'environment_unit_2',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'temperature_c': 32,
        'humidity_percent': 78,
        'pressure_hpa': 1013,
        'voc_level': 'good',
        'voc_reading': 245,
        'uv_index': 9,
        'comfort_score': 3.0,
        'playable': True,
        'warnings': ['high_uv', 'high_heat'],
        'recommendations': ['use_sunscreen', 'stay_hydrated']
    }
})
```

### 3. Feedback Module
**Event:** `FeedbackDataEvent`

Sends:
- Rating feedback (1-5 stars)
- Text feedback (maintenance issues)
- Question responses
- Interaction metadata

**Example (Rating):**
```python
sio.emit('FeedbackDataEvent', {
    'module_id': 'feedback_kiosk_3',
    'court_id': 'basketball_a',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'report_type': 'rating',
        'question_id': 'overall_quality',
        'question_text': 'How would you rate the overall court quality?',
        'rating': 4,
        'rating_scale': '1-5',
        'interaction_time_seconds': 8,
        'gesture_used': True
    }
})
```

**Example (Text):**
```python
sio.emit('FeedbackDataEvent', {
    'module_id': 'feedback_kiosk_3',
    'court_id': 'basketball_a',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'report_type': 'text',
        'question_id': 'maintenance_issue',
        'question_text': 'Report a maintenance issue',
        'text_response': 'Net is broken on the north side',
        'issue_category': 'net_broken',
        'priority': 'medium',
        'interaction_time_seconds': 12,
        'gesture_used': True
    }
})
```

## 🔌 Connecting Your BBBW Module

### Step 1: Install Dependencies
```bash
pip install python-socketio
```

### Step 2: Connect to Server
```python
import socketio
from datetime import datetime

sio = socketio.Client()
SERVER_URL = 'http://192.168.68.73:5000'

@sio.event
def connect():
    print('Connected!')
    # Register your module
    sio.emit('module_register', {
        'module_id': 'your_module_id',
        'module_type': 'crowd_detection',  # or 'environment' or 'feedback'
        'timestamp': datetime.now().isoformat()
    })

try:
    sio.connect(SERVER_URL)
except Exception as e:
    print(f"Connection error: {e}")
```

### Step 3: Send Data
Use the appropriate event name (`CrowdDataEvent`, `EnvironmentDataEvent`, or `FeedbackDataEvent`) and send data in the format shown above.

## 📊 Dashboard Features

- **Real-time Data Display**: See live updates from all connected modules
- **Connection Status**: Monitor which modules are online/offline
- **Activity Log**: View all events and data transmissions
- **Module Counters**: See how many modules of each type are connected
- **Visual Indicators**: Color-coded status indicators and crowd levels

## 🔧 API Endpoint

Get current data via REST API:
```
GET http://192.168.68.73:5000/api/current_data
```

Returns JSON with:
- Current crowd data
- Current environment data
- Recent feedback entries
- Connected modules list
- Timestamp

## 🌐 Network Configuration

- **Server IP:** 192.168.68.73
- **Port:** 5000
- **Protocol:** HTTP/WebSocket (SocketIO)

**Important:** Make sure all BBBW devices and the server PC are on the same network!

## 🐛 Debugging Tips

1. **Check Connection**: Look at the dashboard's "Server Status" indicator
2. **Module Registration**: Check the activity log for "Module connected" messages
3. **Data Reception**: Watch the activity log for "data received" messages
4. **Test Client**: Use `test_client_example.py` to verify server is working

## 📝 Legacy Support

The server still supports legacy events:
- `usage_data` - Equipment usage count
- `volume_data` - Volume alerts

These are maintained for backward compatibility with existing `machine_client.py`.

## 👥 For Group Members

1. **Get the server running** on a shared PC/server
2. **Connect your BBBW** using the examples above
3. **Watch the dashboard** to see your data appear in real-time
4. **Debug together** - everyone can see all modules simultaneously!

## 📚 Additional Resources

- See `test_client_example.py` for complete working examples
- Check `DATA_TRANSMISSION_QUICK_REFERENCE.md` for detailed protocol specs
- Review `DATA_TRANSMISSION_PROTOCOL.md` for full documentation
