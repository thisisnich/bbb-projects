import socketio
import time
import Adafruit_BBIO.GPIO as GPIO
import cv2
import base64
import threading

sio = socketio.Client()
GPIO.setup("P8_10", GPIO.IN)

# Webcam settings
WEBCAM_DEVICE = 0  # OpenCV device index (0 = first camera)
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
WEBCAM_FPS = 15  # Frames per second to send (OpenCV allows much higher rates)
# Note: Using OpenCV direct capture instead of fswebcam for better performance

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

# Global webcam capture object
webcam_cap = None
webcam_lock = threading.Lock()

def init_webcam():
    """Initialize OpenCV webcam capture."""
    global webcam_cap
    try:
        webcam_cap = cv2.VideoCapture(WEBCAM_DEVICE)
        if webcam_cap.isOpened():
            webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
            webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
            webcam_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            print(f'[WEBCAM] Initialized: {WEBCAM_WIDTH}x{WEBCAM_HEIGHT}')
            return True
        else:
            print('[WEBCAM] Failed to open camera')
            return False
    except Exception as e:
        print(f'[WEBCAM] Initialization error: {e}')
        return False

def capture_webcam_frame():
    """Capture a single frame from USB webcam using OpenCV."""
    global webcam_cap
    try:
        with webcam_lock:
            if webcam_cap is None or not webcam_cap.isOpened():
                if not init_webcam():
                    return None
            
            ret, frame = webcam_cap.read()
            
            if not ret or frame is None:
                print('[WEBCAM] Failed to read frame, attempting to reopen...')
                webcam_cap.release()
                time.sleep(0.1)
                if not init_webcam():
                    return None
                ret, frame = webcam_cap.read()
                if not ret or frame is None:
                    return None
            
            # Encode frame as JPEG (85% quality)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            ret, jpeg_bytes = cv2.imencode('.jpg', frame, encode_param)
            
            if ret and jpeg_bytes is not None:
                # Encode as base64 for transmission
                frame_base64 = base64.b64encode(jpeg_bytes.tobytes()).decode('utf-8')
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

# Initialize webcam
if init_webcam():
    # Start webcam streaming thread
    webcam_thread = threading.Thread(target=webcam_stream_thread, daemon=True)
    webcam_thread.start()
    print('Webcam streaming thread started')
else:
    print('[WEBCAM] Warning: Webcam initialization failed, video streaming disabled')

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
