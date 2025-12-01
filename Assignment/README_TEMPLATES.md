# 📡 Working Templates - Smart Sports Facility System

This folder contains working templates for the webcam → webserver → dashboard system.

## 📁 Files

1. **`Module1_CrowdDetection_Client.py`** - BBBW client that captures webcam and sends frames
2. **`CloudServer_WebDashboard.py`** - Flask server that processes video with Google AI
3. **`templates/dashboard.html`** - Web dashboard to display results
4. **`requirements_server.txt`** - Python packages for server
5. **`requirements_client.txt`** - Python packages for client

---

## 🚀 Quick Start

### Step 1: Setup Server (PC/Laptop)

1. **Install dependencies:**
   ```bash
   pip install -r requirements_server.txt
   ```

2. **Set Google AI API Key (optional but recommended):**
   ```bash
   # Windows PowerShell
   $env:GOOGLE_AI_API_KEY="your-api-key-here"
   
   # Linux/Mac
   export GOOGLE_AI_API_KEY="your-api-key-here"
   ```
   
   Or get one from: https://makersuite.google.com/app/apikey

3. **Update server IP address:**
   - Open `CloudServer_WebDashboard.py`
   - Change `SERVER_IP = '192.168.X.X'` to your PC's IP address
   - Find your IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)

4. **Run server:**
   ```bash
   python CloudServer_WebDashboard.py
   ```

5. **Open dashboard:**
   - Open browser to: `http://YOUR_IP:5000`

### Step 2: Setup Client (BeagleBone Black Wireless)

1. **Copy `Module1_CrowdDetection_Client.py` to BBBW:**
   ```bash
   # Use your sync script or SCP
   scp Module1_CrowdDetection_Client.py debian@192.168.X.X:/home/debian/
   ```

2. **Install dependencies on BBBW:**
   
   **Python packages:**
   ```bash
   sudo pip3 install -r requirements_client.txt
   ```
   
   **System packages:**
   ```bash
   sudo apt-get install fswebcam  # Required for webcam capture
   ```
   
   **Note:** `fswebcam` is a system package (not Python), so it must be installed with `apt-get`, not `pip`.

3. **Update configuration:**
   - Open `Module1_CrowdDetection_Client.py`
   - Change `SERVER_URL = 'http://192.168.X.X:5000'` to your server IP
   - Change `COURT_ID` and `MODULE_ID` if needed

4. **Run client:**
   ```bash
   sudo python3 Module1_CrowdDetection_Client.py
   ```

---

## 🔧 Configuration

### Server Configuration

In `CloudServer_WebDashboard.py`:
```python
SERVER_IP = '192.168.X.X'  # Your PC's IP address
SERVER_PORT = 5000
GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')
```

### Client Configuration

In `Module1_CrowdDetection_Client.py`:
```python
SERVER_URL = 'http://192.168.X.X:5000'  # Server IP
COURT_ID = 'basketball_a'
MODULE_ID = 'crowd_unit_1'
WEBCAM_FPS = 2  # Frames per second to send
WEBCAM_DEVICE = 0  # Usually /dev/video0
```

---

## 📊 How It Works

1. **Module 1 (BBBW):**
   - Captures video frames from USB webcam using `fswebcam` (lightweight, no OpenCV)
   - Encodes frames as base64 JPEG
   - Reads MIC, Motion, Proximity sensors
   - Sends `CrowdVideoFrameEvent` to server every 0.5 seconds

2. **Server:**
   - Receives video frames via SocketIO
   - Decodes base64 to image bytes
   - Processes with Google AI API to count people
   - Calculates confidence and crowd level
   - Broadcasts processed data to dashboard

3. **Dashboard:**
   - Connects to server via SocketIO
   - Receives `CrowdDataUpdate` events
   - Displays people count, crowd level, confidence
   - Shows sensor status and activity log

---

## 🧪 Testing Without Hardware

### Test Server Only:

1. Run server: `python CloudServer_WebDashboard.py`
2. Open dashboard: `http://localhost:5000`
3. You'll see "Waiting for data from Module 1"

### Test with Simulated Data:

You can modify the client to send test frames or use a test script.

---

## 🐛 Troubleshooting

### Server Issues:

- **Port already in use:** Change `SERVER_PORT` or kill process using port 5000
- **Google AI not working:** Check API key is set correctly
- **Dashboard not loading:** Check firewall allows port 5000

### Client Issues:

- **Can't connect:** Verify server IP and that server is running
- **Webcam not found:** Check `/dev/video0` exists: `ls -l /dev/video*`
- **fswebcam not found:** Install with: `sudo apt-get install fswebcam`
- **Import errors:** Install dependencies: `sudo pip3 install python-socketio`

### Network Issues:

- **Connection timeout:** Ensure BBBW and PC are on same Wi-Fi network
- **Can't see dashboard:** Check firewall settings on PC

---

## 📝 Next Steps

1. **Implement actual sensor reading:**
   - Replace simulated values in `read_mic_click()`, `read_motion_click()`, `read_proximity_click()`

2. **Add Module 2 (Environment):**
   - Create similar client for environment sensors
   - Add environment data display to dashboard

3. **Add Module 3 (Feedback):**
   - Create feedback client
   - Add feedback display to dashboard

4. **Add Module 4 & 5:**
   - Create dashboard and display clients
   - Connect them to receive processed data

---

## 📚 Documentation

See:
- `DATA_TRANSMISSION_PROTOCOL.md` - Full protocol documentation
- `DATA_TRANSMISSION_QUICK_REFERENCE.md` - Quick reference guide

---

**Last Updated:** 2025-11-17

