"""
Module 1: Crowd Intelligence Unit - Client Template
Captures video frames from USB webcam using fswebcam and sends to cloud server
Also reads MIC, Motion, and Proximity Click sensors
"""
import socketio
import subprocess
import base64
import time
import threading
from datetime import datetime
import sys
import os

# ========== CONFIGURATION ==========
SERVER_URL = 'http://192.168.72.161:5000'  # CHANGE THIS to your server IP
COURT_ID = 'basketball_a'
MODULE_ID = 'crowd_unit_1'
WEBCAM_FPS = 2  # Send 2 frames per second (every 0.5 seconds)
WEBCAM_DEVICE = '/dev/video0'  # USB webcam device path

# ========== GLOBAL VARIABLES ==========
sio = socketio.Client()
is_streaming = False

# ========== SOCKET.IO EVENTS ==========

@sio.event
def connect():
    """Called when connected to server"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 1 connected to server')
    
    # Register this module
    sio.emit('module_register', {
        'module_id': MODULE_ID,
        'module_type': 'crowd_detection',
        'court_id': COURT_ID,
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def disconnect():
    """Called when disconnected from server"""
    global is_streaming
    is_streaming = False
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 1 disconnected from server')

@sio.event
def registration_ack(data):
    """Acknowledgment from server"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Registration confirmed: {data.get("status")}')

# ========== WEBCAM FUNCTIONS (fswebcam) ==========

def check_fswebcam():
    """Check if fswebcam is installed"""
    try:
        result = subprocess.run(['which', 'fswebcam'], 
                              capture_output=True, 
                              timeout=2)
        if result.returncode == 0:
            return True
        else:
            print("[ERROR] fswebcam not found. Install with: sudo apt-get install fswebcam")
            return False
    except Exception as e:
        print(f"[ERROR] Error checking fswebcam: {e}")
        return False

def check_webcam_device():
    """Check if webcam device exists"""
    if os.path.exists(WEBCAM_DEVICE):
        return True
    else:
        print(f"[ERROR] Webcam device {WEBCAM_DEVICE} not found")
        print(f"Available video devices:")
        try:
            result = subprocess.run(['ls', '-la', '/dev/video*'], 
                                  capture_output=True, 
                                  timeout=2)
            print(result.stdout.decode('utf-8'))
        except:
            pass
        return False

def capture_and_encode_frame():
    """Capture frame from webcam using fswebcam and encode as base64 JPEG"""
    try:
        # Capture frame using fswebcam to stdout
        result = subprocess.run([
            'fswebcam',
            '-d', WEBCAM_DEVICE,
            '-r', '640x480',  # Resolution
            '--no-banner',    # No timestamp banner
            '--skip', '2',    # Skip first 2 frames (let camera adjust)
            '--jpeg', '85',   # JPEG quality 85%
            '-'               # Output to stdout
        ], capture_output=True, timeout=3)
        
        if result.returncode == 0 and len(result.stdout) > 0:
            # Encode as base64 for transmission
            frame_base64 = base64.b64encode(result.stdout).decode('utf-8')
            return frame_base64
        else:
            print(f"[WEBCAM] fswebcam failed: returncode={result.returncode}, size={len(result.stdout)}")
            if result.stderr:
                print(f"[WEBCAM] Error: {result.stderr.decode('utf-8')}")
            return None
    except subprocess.TimeoutExpired:
        print("[WEBCAM] Frame capture timeout")
        return None
    except FileNotFoundError:
        print("[WEBCAM] fswebcam not found. Install with: sudo apt-get install fswebcam")
        return None
    except Exception as e:
        print(f'[WEBCAM] Frame capture error: {e}')
        return None

# ========== SENSOR READING FUNCTIONS ==========

def read_mic_click():
    """Read MIC Click sensor - returns noise level in dB"""
    # TODO: Implement actual MIC Click reading
    # For now, return simulated value
    try:
        # Example: Read from ADC or I2C
        # noise_db = read_mic_sensor()
        noise_db = 65  # Simulated value
        return noise_db
    except Exception as e:
        print(f"[MIC] Error reading sensor: {e}")
        return 0

def read_motion_click():
    """Read Motion Click (PIR) sensor - returns True if motion detected"""
    # TODO: Implement actual Motion Click reading
    # For now, return simulated value
    try:
        # Example: Read from GPIO
        # motion = GPIO.input("P8_XX")
        motion = True  # Simulated value
        return motion
    except Exception as e:
        print(f"[MOTION] Error reading sensor: {e}")
        return False

def read_proximity_click():
    """Read Proximity Click sensor - returns True if proximity triggered"""
    # TODO: Implement actual Proximity Click reading
    # For now, return simulated value
    try:
        # Example: Read from I2C
        # proximity = read_proximity_sensor()
        proximity = False  # Simulated value
        return proximity
    except Exception as e:
        print(f"[PROXIMITY] Error reading sensor: {e}")
        return False

# ========== VIDEO STREAMING THREAD ==========

def send_video_frames():
    """Continuously capture and send video frames to server"""
    global is_streaming
    frame_interval = 1.0 / WEBCAM_FPS  # 0.5 seconds for 2 FPS
    
    while is_streaming:
        try:
            if sio.connected:
                # Capture and encode frame
                frame_base64 = capture_and_encode_frame()
                
                if frame_base64:
                    # Read other sensors
                    noise_db = read_mic_click()
                    motion_detected = read_motion_click()
                    proximity_triggered = read_proximity_click()
                    
                    # Send video frame with sensor data
                    sio.emit('CrowdVideoFrameEvent', {
                        'module_id': MODULE_ID,
                        'court_id': COURT_ID,
                        'timestamp': datetime.now().isoformat(),
                        'data': {
                            'video_frame': frame_base64,
                            'noise_db': noise_db,
                            'motion_detected': motion_detected,
                            'proximity_triggered': proximity_triggered,
                            'sensors_status': {
                                'webcam': 'ok',
                                'mic': 'ok',
                                'motion': 'ok',
                                'proximity': 'ok'
                            }
                        }
                    })
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Video frame sent ({len(frame_base64)} bytes), "
                          f"Noise: {noise_db}dB, Motion: {motion_detected}, Proximity: {proximity_triggered}")
                else:
                    print("[WEBCAM] Failed to capture frame")
            else:
                print("[WEBCAM] Not connected to server, waiting...")
                time.sleep(1)
                
        except Exception as e:
            print(f"[WEBCAM] Error sending video frame: {e}")
        
        time.sleep(frame_interval)

# ========== MAIN FUNCTION ==========

def main():
    """Main function"""
    global is_streaming
    
    print("=" * 60)
    print("Module 1: Crowd Intelligence Unit - Client (fswebcam)")
    print("=" * 60)
    print(f"Module ID: {MODULE_ID}")
    print(f"Court ID: {COURT_ID}")
    print(f"Server URL: {SERVER_URL}")
    print(f"Webcam FPS: {WEBCAM_FPS}")
    print(f"Webcam Device: {WEBCAM_DEVICE}")
    print("=" * 60)
    
    # Check fswebcam
    if not check_fswebcam():
        print("[ERROR] fswebcam not available. Exiting.")
        print("Install with: sudo apt-get install fswebcam")
        sys.exit(1)
    
    # Check webcam device
    if not check_webcam_device():
        print("[ERROR] Webcam device not found. Exiting.")
        sys.exit(1)
    
    # Connect to server
    try:
        print(f"\nConnecting to server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        
        # Wait a moment for connection
        time.sleep(1)
        
        if sio.connected:
            print("Connected! Starting video stream...")
            is_streaming = True
            
            # Start video streaming thread
            video_thread = threading.Thread(target=send_video_frames, daemon=True)
            video_thread.start()
            
            # Keep main thread alive
            print("Streaming video frames. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
                is_streaming = False
                time.sleep(1)
        else:
            print("[ERROR] Failed to connect to server")
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        # Cleanup
        is_streaming = False
        if sio.connected:
            sio.disconnect()
        print("Client disconnected. Goodbye!")

if __name__ == '__main__':
    main()

