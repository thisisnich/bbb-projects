import socketio
import time
import Adafruit_BBIO.GPIO as GPIO
import subprocess
import base64
import threading

sio = socketio.Client()
GPIO.setup("P8_10", GPIO.IN)

# Webcam settings
WEBCAM_DEVICE = '/dev/video0'
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
WEBCAM_FPS = 5  # Frames per second to send

@sio.event
def connect():
    print('Connection established.')

@sio.event
def disconnect():
    print('Disconnected from server')

# Connect to server
while True:
    try:
        sio.connect('http://192.168.72.161:5000')
        break
    except:
        print("Try to connect to the server.")
        pass

def capture_webcam_frame():
    """Capture a single frame from USB webcam using fswebcam."""
    try:
        result = subprocess.run([
            'fswebcam',
            '-d', WEBCAM_DEVICE,
            '-r', f'{WEBCAM_WIDTH}x{WEBCAM_HEIGHT}',
            '--no-banner',
            '--skip', '2',
            '--jpeg', '85',
            '-'
        ], capture_output=True, timeout=3)
        
        if result.returncode == 0 and len(result.stdout) > 0:
            # Encode frame as base64 for transmission
            frame_base64 = base64.b64encode(result.stdout).decode('utf-8')
            return frame_base64
    except Exception as e:
        print(f'[WEBCAM] Frame capture error: {e}')
    return None

def webcam_stream_thread():
    """Thread function to continuously capture and send webcam frames."""
    frame_interval = 1.0 / WEBCAM_FPS
    
    while True:
        try:
            if sio.connected:
                frame = capture_webcam_frame()
                if frame:
                    sio.emit('BBBW4VideoFrame', {'data': frame})
            time.sleep(frame_interval)
        except Exception as e:
            print(f'[WEBCAM] Stream error: {e}')
            time.sleep(1)

# Start webcam streaming thread
webcam_thread = threading.Thread(target=webcam_stream_thread, daemon=True)
webcam_thread.start()
print('Webcam streaming thread started')

# Main loop for door detection
PreviousDoorDetectionStatus = 0

while True:
    try:
        CurrentDoorDetectionStatus = GPIO.input("P8_10")
        if CurrentDoorDetectionStatus:
            print("Magnet is Detected (Door Closed)")
        else:
            print("No Magnet is Detected (Door Opened)")
        if (abs(CurrentDoorDetectionStatus - PreviousDoorDetectionStatus) > 0):
            sio.emit('BBBW4Event', {'data': CurrentDoorDetectionStatus})
            print('Data sent!')
        PreviousDoorDetectionStatus = CurrentDoorDetectionStatus
    except:
        print('Unable to transmit data.')
        pass
    time.sleep(0.5)
