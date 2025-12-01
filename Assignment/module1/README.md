# Module 1: Crowd Intelligence Unit

## Overview
Captures video frames from USB webcam and sends to cloud server for processing. Also reads MIC, Motion, and Proximity Click sensors.

## Files
- `Module1_CrowdDetection_Client.py` - Main client code

## Setup

### 1. Install Dependencies

**Python packages:**
```bash
sudo pip3 install -r ../requirements_client.txt
```

**System packages:**
```bash
sudo apt-get install fswebcam
```

**Note:** fswebcam is a system package (not a Python package), so it must be installed separately with `apt-get`.

### 2. Configuration
Edit `Module1_CrowdDetection_Client.py` and update:
- `SERVER_URL` - Your cloud server IP address
- `COURT_ID` - Court identifier
- `MODULE_ID` - Module identifier
- `WEBCAM_DEVICE` - Webcam device path (usually `/dev/video0`)

### 3. Run
```bash
sudo python3 Module1_CrowdDetection_Client.py
```

## Hardware
- BeagleBone Black Wireless
- USB Webcam
- MIC Click
- Motion Click
- Proximity Click
- OLED Click

## Data Transmission
- Sends video frames every 0.5 seconds (2 FPS)
- Sends sensor data (noise, motion, proximity) with each frame
- Uses SocketIO to communicate with cloud server

